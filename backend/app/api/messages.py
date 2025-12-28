# backend/app/api/messages.py

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime
import json
from ..database import get_db
from ..models import User, Lead, Message, Bot
from ..auth import require_manager
from ..telegram_handler import send_telegram_message

router = APIRouter(prefix="/messages", tags=["messages"])


class MessageResponse(BaseModel):
    id: int
    sender: str
    text: str
    created_at: datetime

    class Config:
        from_attributes = True


class SendMessageRequest(BaseModel):
    text: str


@router.get("/{lead_id}", response_model=List[MessageResponse])
async def get_messages(
        lead_id: int,
        current_user: User = Depends(require_manager),
        db: Session = Depends(get_db)
):
    """Получить историю сообщений лида"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if current_user.role == "manager":
        if lead.assigned_manager_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

    messages = db.query(Message).filter(
        Message.lead_id == lead_id
    ).order_by(Message.created_at).all()

    return messages


@router.post("/{lead_id}/send")
async def send_message(
        lead_id: int,
        request: SendMessageRequest,
        current_user: User = Depends(require_manager),
        db: Session = Depends(get_db)
):
    """Отправить сообщение лиду"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if current_user.role == "manager":
        if lead.assigned_manager_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

    if lead.status == "closed":
        raise HTTPException(status_code=400, detail="Lead is closed")

    bot = db.query(Bot).filter(Bot.id == lead.bot_id).first()
    if not bot:
        raise HTTPException(status_code=500, detail="Bot not configured")

    success = await send_telegram_message(bot.token, lead.telegram_chat_id, request.text)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to send message")

    new_message = Message(
        lead_id=lead.id,
        sender="manager",
        text=request.text,
        created_at=datetime.utcnow()
    )
    db.add(new_message)

    # Меняем статус на "in_progress" и обновляем last_updated_at
    lead.status = "in_progress"
    lead.last_updated_at = datetime.utcnow()

    db.commit()
    db.refresh(new_message)

    from ..websocket import manager as ws_manager
    await ws_manager.notify_new_message(
        lead_id=lead.id,
        manager_id=current_user.id,
        message_data={
            "id": new_message.id,
            "text": request.text,
            "sender": "manager",
            "created_at": new_message.created_at.isoformat()
        }
    )

    return {
        "status": "sent",
        "message": {
            "id": new_message.id,
            "text": new_message.text,
            "sender": "manager",
            "created_at": new_message.created_at.isoformat()
        }
    }


@router.websocket("/ws/{lead_id}")
async def websocket_chat(websocket: WebSocket, lead_id: int):
    """WebSocket для real-time чата с лидом"""
    await websocket.accept()
    user = None

    try:
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=4001)
            return

        from jose import jwt, JWTError
        from ..config import settings

        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            username = payload.get("sub")

            db = next(get_db())

            user = db.query(User).filter(User.username == username).first()

            if not user or user.role not in ["admin", "manager"]:
                await websocket.close(code=4003)
                return

            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if not lead:
                await websocket.close(code=4004)
                return

            if user.role == "manager":
                if lead.assigned_manager_id != user.id:
                    await websocket.close(code=4003)
                    return

            from ..websocket import manager as ws_manager
            await ws_manager.connect(user.id, websocket)

            while True:
                data = await websocket.receive_text()
                message_data = json.loads(data)

                if message_data.get("action") == "send_message":
                    text = message_data.get("text")

                    if lead.status == "closed":
                        await websocket.send_json({
                            "type": "error",
                            "message": "Lead is closed"
                        })
                        continue

                    bot = db.query(Bot).filter(Bot.id == lead.bot_id).first()
                    if not bot:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Bot not configured"
                        })
                        continue

                    success = await send_telegram_message(
                        bot.token,
                        lead.telegram_chat_id,
                        text
                    )

                    if not success:
                        await websocket.send_json({
                            "type": "error",
                            "message": "Failed to send message"
                        })
                        continue

                    new_message = Message(
                        lead_id=lead.id,
                        sender="manager",
                        text=text,
                        created_at=datetime.utcnow()
                    )
                    db.add(new_message)

                    # Меняем статус на "in_progress" и обновляем last_updated_at
                    lead.status = "in_progress"
                    lead.last_updated_at = datetime.utcnow()

                    db.commit()
                    db.refresh(new_message)

                    await websocket.send_json({
                        "type": "message_sent",
                        "message": {
                            "id": new_message.id,
                            "text": text,
                            "sender": "manager",
                            "created_at": new_message.created_at.isoformat()
                        }
                    })

        except JWTError:
            await websocket.close(code=4003)
            return

    except WebSocketDisconnect:
        if user:
            from ..websocket import manager as ws_manager
            ws_manager.disconnect(user.id)
    except Exception as e:
        import logging
        logging.error(f"WebSocket error: {e}")
        if user:
            from ..websocket import manager as ws_manager
            ws_manager.disconnect(user.id)