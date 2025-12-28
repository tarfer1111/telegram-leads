# tests/test_api_stats.py

import pytest
from backend.app.models import Lead, Message


def test_overview_stats_admin(client, admin_token, db_session, project1, bot1,
                              manager1, manager2):
    """Админ видит общую статистику по всем проектам"""
    lead1 = Lead(telegram_chat_id=111, bot_id=bot1.id, project_id=project1.id,
                 assigned_manager_id=manager1.id, status="active")
    lead2 = Lead(telegram_chat_id=222, bot_id=bot1.id, project_id=project1.id,
                 assigned_manager_id=manager2.id, status="closed")
    db_session.add_all([lead1, lead2])
    db_session.flush()

    msg1 = Message(lead_id=lead1.id, sender="lead", text="Hi")
    msg2 = Message(lead_id=lead2.id, sender="manager", text="Hello")
    db_session.add_all([msg1, msg2])
    db_session.commit()

    response = client.get("/stats/overview", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["total_leads"] == 2
    assert data["active_leads"] == 1
    assert data["closed_leads"] == 1
    assert data["total_messages"] == 2


def test_overview_stats_manager(client, manager1_token, db_session,
                                project1, project2, bot1, manager1, manager2):
    """Менеджер видит статистику только по своим проектам"""
    project1.managers.append(manager1)

    from backend.app.models import Bot
    bot2 = Bot(identifier="bot2", name="Bot 2", project_id=project2.id,
               token="token2", auto_reply="Hi", is_active=True)
    db_session.add(bot2)
    db_session.flush()

    # Лид в project1 (менеджер видит)
    lead1 = Lead(telegram_chat_id=111, bot_id=bot1.id, project_id=project1.id,
                 assigned_manager_id=manager1.id, status="active")
    # Лид в project2 (менеджер НЕ видит)
    lead2 = Lead(telegram_chat_id=222, bot_id=bot2.id, project_id=project2.id,
                 assigned_manager_id=manager2.id, status="active")
    db_session.add_all([lead1, lead2])
    db_session.commit()

    response = client.get("/stats/overview", headers={
        "Authorization": f"Bearer {manager1_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["total_leads"] == 1


def test_manager_stats(client, admin_token, db_session, project1, bot1,
                       manager1):
    """Статистика по конкретному менеджеру"""
    project1.managers.append(manager1)

    lead1 = Lead(telegram_chat_id=111, bot_id=bot1.id, project_id=project1.id,
                 assigned_manager_id=manager1.id, status="active")
    lead2 = Lead(telegram_chat_id=222, bot_id=bot1.id, project_id=project1.id,
                 assigned_manager_id=manager1.id, status="closed")
    db_session.add_all([lead1, lead2])
    db_session.flush()

    msg = Message(lead_id=lead1.id, sender="manager", text="Test")
    db_session.add(msg)
    db_session.commit()

    response = client.get(f"/stats/manager/{manager1.id}", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["manager_id"] == manager1.id
    assert data["total_leads"] == 2
    assert data["active_leads"] == 1
    assert data["closed_leads"] == 1


def test_manager_cannot_see_other_manager_stats(client, manager1_token,
                                                manager2):
    """Менеджер не может видеть статистику другого менеджера"""
    response = client.get(f"/stats/manager/{manager2.id}", headers={
        "Authorization": f"Bearer {manager1_token}"
    })
    assert response.status_code == 403


def test_manager_can_see_own_stats(client, manager1_token, db_session,
                                   project1, bot1, manager1):
    """Менеджер может видеть свою статистику"""
    project1.managers.append(manager1)
    db_session.commit()

    response = client.get(f"/stats/manager/{manager1.id}", headers={
        "Authorization": f"Bearer {manager1_token}"
    })
    assert response.status_code == 200