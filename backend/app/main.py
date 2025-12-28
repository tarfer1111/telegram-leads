# backend/app/main.py

from fastapi import FastAPI, Request, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import logging
from .database import get_db
from .api import auth, admin, leads, messages, stats
from .telegram_handler import handle_start_command, handle_incoming_message
from .websocket import manager as ws_manager
from .models import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Telegram Leads System",
    description="Система распределения лидов из Telegram",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(leads.router)
app.include_router(messages.router)
app.include_router(stats.router)


@app.get("/")
async def root():
    return {
        "message": "Telegram Leads System API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """WebSocket endpoint для real-time уведомлений"""
    manager_id = None
    try:
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=4001)
            return

        from jose import jwt, JWTError
        from .config import settings

        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            username = payload.get("sub")
            user = db.query(User).filter(User.username == username).first()

            if not user or user.role not in ["admin", "manager"]:
                await websocket.close(code=4003)
                return

            manager_id = user.id
        except JWTError:
            await websocket.close(code=4003)
            return

        await ws_manager.connect(manager_id, websocket)

        while True:
            data = await websocket.receive_text()
            logger.info(f"Received from manager {manager_id}: {data}")

    except WebSocketDisconnect:
        if manager_id:
            ws_manager.disconnect(manager_id)
        logger.info(f"Manager {manager_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if manager_id:
            ws_manager.disconnect(manager_id)


@app.post("/webhook/{bot_identifier}")
async def telegram_webhook(
        bot_identifier: str,
        request: Request,
        db: Session = Depends(get_db)
):
    """Endpoint для обработки вебхуков от Telegram ботов"""
    try:
        data = await request.json()
        logger.info(f"Received webhook from {bot_identifier}: {data}")

        if "message" not in data:
            return {"ok": True}

        message = data["message"]
        text = message.get("text", "")

        if text.startswith("/start"):
            result = await handle_start_command(db, bot_identifier, data)
            logger.info(f"Start command result: {result}")
            return {"ok": True, "result": result}
        else:
            result = await handle_incoming_message(db, bot_identifier, data)
            logger.info(f"Message handling result: {result}")
            return {"ok": True, "result": result}

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {"ok": False, "error": str(e)}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    from .config import settings

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )