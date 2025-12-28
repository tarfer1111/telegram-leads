# backend/app/api/leads.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime
from ..database import get_db
from ..models import User, Lead
from ..auth import require_manager

router = APIRouter(prefix="/leads", tags=["leads"])


class LeadResponse(BaseModel):
    id: int
    telegram_chat_id: int
    telegram_username: str | None
    telegram_first_name: str | None
    telegram_last_name: str | None
    bot_id: int
    project_id: int
    project_name: str
    assigned_manager_id: int
    status: str
    created_at: datetime
    last_updated_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=List[LeadResponse])
async def get_leads(
        status: str | None = None,
        current_user: User = Depends(require_manager),
        db: Session = Depends(get_db)
):
    """Получить список лидов"""
    query = db.query(Lead)

    if current_user.role == "manager":
        query = query.filter(Lead.assigned_manager_id == current_user.id)

    if status:
        query = query.filter(Lead.status == status)

    leads = query.order_by(Lead.created_at.desc()).all()

    result = []
    for lead in leads:
        lead_dict = {
            "id": lead.id,
            "telegram_chat_id": lead.telegram_chat_id,
            "telegram_username": lead.telegram_username,
            "telegram_first_name": lead.telegram_first_name,
            "telegram_last_name": lead.telegram_last_name,
            "bot_id": lead.bot_id,
            "project_id": lead.project_id,
            "project_name": lead.project.name,
            "assigned_manager_id": lead.assigned_manager_id,
            "status": lead.status,
            "created_at": lead.created_at,
            "last_updated_at": lead.last_updated_at
        }
        result.append(lead_dict)

    return result


@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(
        lead_id: int,
        current_user: User = Depends(require_manager),
        db: Session = Depends(get_db)
):
    """Получить детали лида"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if current_user.role == "manager":
        if lead.assigned_manager_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

    return {
        "id": lead.id,
        "telegram_chat_id": lead.telegram_chat_id,
        "telegram_username": lead.telegram_username,
        "telegram_first_name": lead.telegram_first_name,
        "telegram_last_name": lead.telegram_last_name,
        "bot_id": lead.bot_id,
        "project_id": lead.project_id,
        "project_name": lead.project.name,
        "assigned_manager_id": lead.assigned_manager_id,
        "status": lead.status,
        "created_at": lead.created_at,
        "last_updated_at": lead.last_updated_at
    }


@router.put("/{lead_id}/mark-read")
async def mark_lead_as_read(
        lead_id: int,
        current_user: User = Depends(require_manager),
        db: Session = Depends(get_db)
):
    """Пометить лида как прочитанного (new -> read)"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if current_user.role == "manager":
        if lead.assigned_manager_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

    if lead.status == "closed":
        raise HTTPException(status_code=400, detail="Cannot mark closed lead as read")

    lead.status = "read"
    lead.last_updated_at = datetime.utcnow()
    db.commit()

    return {"status": "read", "lead_id": lead_id}


@router.put("/{lead_id}/close")
async def close_lead(
        lead_id: int,
        current_user: User = Depends(require_manager),
        db: Session = Depends(get_db)
):
    """Закрыть лида"""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()

    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if current_user.role == "manager":
        if lead.assigned_manager_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

    lead.status = "closed"
    lead.closed_at = datetime.utcnow()
    lead.last_updated_at = datetime.utcnow()
    db.commit()

    return {"status": "closed", "lead_id": lead_id}