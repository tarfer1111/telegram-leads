# backend/app/telegram_handler.py

import httpx
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from .models import Lead, Message, Bot
from .distribution import get_next_manager
from .config import settings

logger = logging.getLogger(__name__)


async def set_telegram_webhook(bot_token: str, bot_identifier: str) -> bool:
    """Установка вебхука для бота"""
    webhook_url = f"{settings.BASE_URL}/webhook/{bot_identifier}"
    url = f"https://api.telegram.org/bot{bot_token}/setWebhook"

    payload = {
        "url": webhook_url,
        "allowed_updates": ["message"]
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            if response.status_code == 200:
                logger.info(f"Webhook set for {bot_identifier}: {webhook_url}")
                return True
            else:
                logger.error(f"Failed to set webhook: {response.text}")
                return False
    except Exception as e:
        logger.error(f"Error setting webhook: {e}")
        return False


async def send_telegram_message(bot_token: str, chat_id: int,
                                text: str) -> bool:
    """Отправка сообщения через Telegram API"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, timeout=10.0)
            if response.status_code == 200:
                logger.info(f"Message sent to chat_id {chat_id}")
                return True
            else:
                logger.error(f"Failed to send message: {response.text}")
                return False
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return False


async def handle_start_command(db: Session, bot_identifier: str,
                               telegram_data: dict) -> dict:
    """Обработка команды /start"""
    message = telegram_data.get("message", {})
    chat = message.get("chat", {})
    from_user = message.get("from", {})

    telegram_chat_id = chat.get("id")
    telegram_username = from_user.get("username")
    telegram_first_name = from_user.get("first_name")
    telegram_last_name = from_user.get("last_name")

    bot = db.query(Bot).filter(Bot.identifier == bot_identifier).first()
    if not bot:
        raise ValueError(f"Bot {bot_identifier} not found")

    existing_lead = db.query(Lead).filter(
        Lead.telegram_chat_id == telegram_chat_id).first()

    if existing_lead:
        logger.info(
            f"Lead already exists for chat_id {telegram_chat_id}, saving message")

        start_message = Message(
            lead_id=existing_lead.id,
            sender="lead",
            text="/start",
            created_at=datetime.utcnow()
        )
        db.add(start_message)

        if existing_lead.status != "closed":
            existing_lead.status = "new"
            existing_lead.last_updated_at = datetime.utcnow()

        db.commit()
        db.refresh(start_message)

        from .websocket import manager as ws_manager
        await ws_manager.notify_new_message(
            lead_id=existing_lead.id,
            manager_id=existing_lead.assigned_manager_id,
            message_data={
                "id": start_message.id,
                "text": "/start",
                "sender": "lead",
                "created_at": start_message.created_at.isoformat()
            }
        )

        return {"status": "exists", "lead_id": existing_lead.id}

    manager = get_next_manager(db, bot.project_id)

    new_lead = Lead(
        telegram_chat_id=telegram_chat_id,
        telegram_username=telegram_username,
        telegram_first_name=telegram_first_name,
        telegram_last_name=telegram_last_name,
        bot_id=bot.id,
        project_id=bot.project_id,
        assigned_manager_id=manager.id,
        status="new",
        created_at=datetime.utcnow(),
        last_updated_at=datetime.utcnow()
    )
    db.add(new_lead)
    db.flush()

    first_message = Message(
        lead_id=new_lead.id,
        sender="lead",
        text="/start",
        created_at=datetime.utcnow()
    )
    db.add(first_message)
    db.commit()
    db.refresh(first_message)

    from .websocket import manager as ws_manager
    await ws_manager.notify_new_message(
        lead_id=new_lead.id,
        manager_id=manager.id,
        message_data={
            "id": first_message.id,
            "text": "/start",
            "sender": "lead",
            "created_at": first_message.created_at.isoformat()
        }
    )

    if bot.auto_reply:
        await send_telegram_message(bot.token, telegram_chat_id,
                                    bot.auto_reply)

        auto_reply_message = Message(
            lead_id=new_lead.id,
            sender="manager",
            text=bot.auto_reply,
            created_at=datetime.utcnow()
        )
        db.add(auto_reply_message)
        db.commit()
        db.refresh(auto_reply_message)

        await ws_manager.notify_new_message(
            lead_id=new_lead.id,
            manager_id=manager.id,
            message_data={
                "id": auto_reply_message.id,
                "text": bot.auto_reply,
                "sender": "manager",
                "created_at": auto_reply_message.created_at.isoformat()
            }
        )

    logger.info(
        f"New lead {new_lead.id} assigned to manager {manager.username}")

    return {
        "status": "created",
        "lead_id": new_lead.id,
        "assigned_to": manager.username
    }


async def handle_incoming_message(db: Session, bot_identifier: str,
                                  telegram_data: dict) -> dict:
    """Обработка входящего сообщения от лида"""
    message = telegram_data.get("message", {})
    chat = message.get("chat", {})
    text = message.get("text", "")

    telegram_chat_id = chat.get("id")

    lead = db.query(Lead).filter(
        Lead.telegram_chat_id == telegram_chat_id).first()
    if not lead:
        logger.warning(f"Lead not found for chat_id {telegram_chat_id}")
        return {"status": "lead_not_found"}

    new_message = Message(
        lead_id=lead.id,
        sender="lead",
        text=text,
        created_at=datetime.utcnow()
    )
    db.add(new_message)

    if lead.status != "closed":
        lead.status = "new"
        lead.last_updated_at = datetime.utcnow()

    db.commit()
    db.refresh(new_message)

    logger.info(f"Message saved for lead {lead.id}")

    from .websocket import manager as ws_manager
    await ws_manager.notify_new_message(
        lead_id=lead.id,
        manager_id=lead.assigned_manager_id,
        message_data={
            "id": new_message.id,
            "text": text,
            "sender": "lead",
            "created_at": new_message.created_at.isoformat()
        }
    )

    return {
        "status": "saved",
        "lead_id": lead.id,
        "message_id": new_message.id
    }