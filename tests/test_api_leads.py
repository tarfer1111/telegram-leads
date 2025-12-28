# tests/test_api_leads.py

import pytest
from backend.app.models import Lead


def test_admin_sees_all_leads(client, admin_token, db_session, project1,
                              project2, bot1, manager1, manager2):
    """Админ видит все лиды всех проектов"""
    # Создаем ботов и лиды для разных проектов
    from backend.app.models import Bot
    bot2 = Bot(identifier="bot2", name="Bot 2", project_id=project2.id,
               token="token2", auto_reply="Hi", is_active=True)
    db_session.add(bot2)
    db_session.flush()

    lead1 = Lead(telegram_chat_id=111, bot_id=bot1.id, project_id=project1.id,
                 assigned_manager_id=manager1.id, status="active")
    lead2 = Lead(telegram_chat_id=222, bot_id=bot2.id, project_id=project2.id,
                 assigned_manager_id=manager2.id, status="active")
    db_session.add_all([lead1, lead2])
    db_session.commit()

    response = client.get("/leads", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_manager_sees_only_own_project_leads(client, manager1_token,
                                             db_session,
                                             project1, project2, bot1,
                                             manager1, manager2):
    """Менеджер видит только лиды своего проекта"""
    # Назначаем manager1 на project1
    project1.managers.append(manager1)

    # Создаем бот для project2
    from backend.app.models import Bot
    bot2 = Bot(identifier="bot2", name="Bot 2", project_id=project2.id,
               token="token2", auto_reply="Hi", is_active=True)
    db_session.add(bot2)
    db_session.flush()

    # Лид в project1 (менеджер должен видеть)
    lead1 = Lead(telegram_chat_id=111, bot_id=bot1.id, project_id=project1.id,
                 assigned_manager_id=manager1.id, status="active")
    # Лид в project2 (менеджер НЕ должен видеть)
    lead2 = Lead(telegram_chat_id=222, bot_id=bot2.id, project_id=project2.id,
                 assigned_manager_id=manager2.id, status="active")
    db_session.add_all([lead1, lead2])
    db_session.commit()

    response = client.get("/leads", headers={
        "Authorization": f"Bearer {manager1_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["telegram_chat_id"] == 111


def test_manager_no_projects_sees_nothing(client, manager1_token):
    """Менеджер без проектов не видит лиды"""
    response = client.get("/leads", headers={
        "Authorization": f"Bearer {manager1_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


def test_get_leads_filter_by_status(client, admin_token, db_session, project1,
                                    bot1, manager1):
    """Фильтр по статусу"""
    lead1 = Lead(telegram_chat_id=111, bot_id=bot1.id, project_id=project1.id,
                 assigned_manager_id=manager1.id, status="active")
    lead2 = Lead(telegram_chat_id=222, bot_id=bot1.id, project_id=project1.id,
                 assigned_manager_id=manager1.id, status="closed")
    db_session.add_all([lead1, lead2])
    db_session.commit()

    response = client.get("/leads?status=active", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status"] == "active"


def test_get_lead_details(client, admin_token, db_session, project1, bot1,
                          manager1):
    """Получение деталей лида"""
    lead = Lead(telegram_chat_id=111, bot_id=bot1.id, project_id=project1.id,
                assigned_manager_id=manager1.id, status="active")
    db_session.add(lead)
    db_session.commit()

    response = client.get(f"/leads/{lead.id}", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["telegram_chat_id"] == 111


def test_manager_cannot_access_other_project_lead(client, manager1_token,
                                                  db_session,
                                                  project1, project2, bot1,
                                                  manager1, manager2):
    """Менеджер не может получить доступ к лиду из чужого проекта"""
    # manager1 в project1
    project1.managers.append(manager1)

    # Создаем бот для project2
    from backend.app.models import Bot
    bot2 = Bot(identifier="bot2", name="Bot 2", project_id=project2.id,
               token="token2", auto_reply="Hi", is_active=True)
    db_session.add(bot2)
    db_session.flush()

    # Лид в project2
    lead = Lead(telegram_chat_id=222, bot_id=bot2.id, project_id=project2.id,
                assigned_manager_id=manager2.id, status="active")
    db_session.add(lead)
    db_session.commit()

    response = client.get(f"/leads/{lead.id}", headers={
        "Authorization": f"Bearer {manager1_token}"
    })
    assert response.status_code == 403


def test_close_lead(client, manager1_token, db_session, project1, bot1,
                    manager1):
    """Закрытие лида"""
    project1.managers.append(manager1)
    lead = Lead(telegram_chat_id=111, bot_id=bot1.id, project_id=project1.id,
                assigned_manager_id=manager1.id, status="active")
    db_session.add(lead)
    db_session.commit()

    response = client.put(f"/leads/{lead.id}/close", headers={
        "Authorization": f"Bearer {manager1_token}"
    })
    assert response.status_code == 200

    # Проверяем что статус изменился
    db_session.refresh(lead)
    assert lead.status == "closed"
    assert lead.closed_at is not None


def test_lead_not_found(client, admin_token):
    """Лид не существует"""
    response = client.get("/leads/99999", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 404