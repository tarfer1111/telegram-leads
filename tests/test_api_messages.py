# tests/test_api_messages.py

import pytest
from backend.app.models import Lead, Message


def test_get_messages(client, manager1_token, db_session, project1, bot1,
                      manager1):
    """Получение истории сообщений"""
    project1.managers.append(manager1)

    lead = Lead(telegram_chat_id=111, bot_id=bot1.id, project_id=project1.id,
                assigned_manager_id=manager1.id, status="active")
    db_session.add(lead)
    db_session.flush()

    msg1 = Message(lead_id=lead.id, sender="lead", text="Hello")
    msg2 = Message(lead_id=lead.id, sender="manager", text="Hi there")
    db_session.add_all([msg1, msg2])
    db_session.commit()

    response = client.get(f"/messages/{lead.id}", headers={
        "Authorization": f"Bearer {manager1_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["sender"] == "lead"
    assert data[1]["sender"] == "manager"


def test_manager_cannot_access_other_project_messages(client, manager1_token,
                                                      db_session,
                                                      project1, project2, bot1,
                                                      manager1, manager2):
    """Менеджер не может читать сообщения из чужого проекта"""
    project1.managers.append(manager1)

    from backend.app.models import Bot
    bot2 = Bot(identifier="bot2", name="Bot 2", project_id=project2.id,
               token="token2", auto_reply="Hi", is_active=True)
    db_session.add(bot2)
    db_session.flush()

    lead = Lead(telegram_chat_id=222, bot_id=bot2.id, project_id=project2.id,
                assigned_manager_id=manager2.id, status="active")
    db_session.add(lead)
    db_session.commit()

    response = client.get(f"/messages/{lead.id}", headers={
        "Authorization": f"Bearer {manager1_token}"
    })
    assert response.status_code == 403


def test_messages_lead_not_found(client, admin_token):
    """Лид не существует"""
    response = client.get("/messages/99999", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 404