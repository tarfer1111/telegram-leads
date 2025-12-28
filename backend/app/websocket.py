# backend/app/websocket.py

import logging
from typing import Dict
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, manager_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[manager_id] = websocket
        logger.info(f"Manager {manager_id} connected via WebSocket")

    def disconnect(self, manager_id: int):
        if manager_id in self.active_connections:
            del self.active_connections[manager_id]
            logger.info(f"Manager {manager_id} disconnected")

    async def send_personal_message(self, manager_id: int, message: dict):
        if manager_id in self.active_connections:
            websocket = self.active_connections[manager_id]
            try:
                await websocket.send_json(message)
                logger.info(f"Sent message to manager {manager_id}")
            except Exception as e:
                logger.error(f"Error sending message to manager {manager_id}: {e}")
                self.disconnect(manager_id)

    async def notify_new_message(self, lead_id: int, manager_id: int, message_data: dict):
        """Уведомить менеджера о новом сообщении от лида"""
        notification = {
            "type": "new_message",
            "lead_id": lead_id,
            "message": message_data
        }
        await self.send_personal_message(manager_id, notification)


manager = ConnectionManager()