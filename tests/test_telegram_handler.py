# tests/test_telegram_handler.py

import pytest
from backend.app.telegram_handler import handle_start_command, \
    handle_incoming_message
from backend.app.models import Lead, Message, Bot


@pytest.mark.asyncio
async def test_handle_start_new_lead(db_session, project1, bot1, manager1):
    """Новый лид через /start"""
    project1.managers.append(manager1)
    db_session.commit()

    telegram_data = {
        "message": {
            "chat": {"id": 12345},
            "from": {
                "username": "testuser",
                "first_name": "Test",
                "last_name": "User"
            },
            "text": "/start"
        }
    }

    result = await handle_start_command(db_session, "bot1", telegram_data)

    assert result["status"] == "created"
    assert "lead_id" in result

    lead = db_session.query(Lead).filter(
        Lead.telegram_chat_id == 12345).first()
    assert lead is not None
    assert lead.telegram_username == "testuser"
    assert lead.assigned_manager_id == manager1.id
    assert lead.project_id == project1.id


@pytest.mark.asyncio
async def test_handle_start_existing_lead(db_session, project1, bot1,
                                          manager1):
    """Существующий лид снова отправил /start"""
    project1.managers.append(manager1)

    lead = Lead(telegram_chat_id=12345, bot_id=bot1.id, project_id=project1.id,
                assigned_manager_id=manager1.id, status="active")
    db_session.add(lead)
    db_session.commit()

    telegram_data = {
        "message": {
            "chat": {"id": 12345},
            "from": {"username": "testuser"},
            "text": "/start"
        }
    }

    result = await handle_start_command(db_session, "bot1", telegram_data)

    assert result["status"] == "exists"
    assert result["lead_id"] == lead.id


@pytest.mark.asyncio
async def test_handle_start_round_robin(db_session, project1, bot1, manager1,
                                        manager2):
    """Round-robin распределение при /start"""
    project1.managers.extend([manager1, manager2])
    db_session.commit()

    # Первый лид
    telegram_data1 = {
        "message": {
            "chat": {"id": 111},
            "from": {"username": "user1"},
            "text": "/start"
        }
    }
    await handle_start_command(db_session, "bot1", telegram_data1)

    # Второй лид
    telegram_data2 = {
        "message": {
            "chat": {"id": 222},
            "from": {"username": "user2"},
            "text": "/start"
        }
    }
    await handle_start_command(db_session, "bot1", telegram_data2)

    lead1 = db_session.query(Lead).filter(Lead.telegram_chat_id == 111).first()
    lead2 = db_session.query(Lead).filter(Lead.telegram_chat_id == 222).first()

    # Проверяем что лиды назначены разным менеджерам
    assert lead1.assigned_manager_id != lead2.assigned_manager_id


@pytest.mark.asyncio
async def test_handle_incoming_message(db_session, project1, bot1, manager1):
    """Входящее сообщение от лида"""
    lead = Lead(telegram_chat_id=12345, bot_id=bot1.id, project_id=project1.id,
                assigned_manager_id=manager1.id, status="active")
    db_session.add(lead)
    db_session.commit()

    telegram_data = {
        "message": {
            "chat": {"id": 12345},
            "text": "Hello from lead"
        }
    }

    result = await handle_incoming_message(db_session, "bot1", telegram_data)

    assert result["status"] == "saved"
    assert result["lead_id"] == lead.id

    messages = db_session.query(Message).filter(
        Message.lead_id == lead.id).all()
    assert len(messages) == 1
    assert messages[0].text == "Hello from lead"
    assert messages[0].sender == "lead"


@pytest.mark.asyncio
async def test_handle_message_lead_not_found(db_session):
    """Сообщение от несуществующего лида"""
    telegram_data = {
        "message": {
            "chat": {"id": 99999},
            "text": "Test"
        }
    }

    result = await handle_incoming_message(db_session, "bot1", telegram_data)

    assert result["status"] == "lead_not_found"


@pytest.mark.asyncio
async def test_handle_start_bot_not_found(db_session):
    """Бот не найден"""
    telegram_data = {
        "message": {
            "chat": {"id": 12345},
            "from": {"username": "test"},
            "text": "/start"
        }
    }

    with pytest.raises(ValueError):
        await handle_start_command(db_session, "nonexistent", telegram_data)