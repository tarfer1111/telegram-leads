# backend/app/api/stats.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime, timedelta
from ..database import get_db
from ..models import User, Lead, Message
from ..auth import require_manager, require_admin

router = APIRouter(prefix="/stats", tags=["stats"])


class OverviewStats(BaseModel):
    total_leads: int
    active_leads: int
    closed_leads: int
    total_messages: int
    managers_count: int


class ManagerStats(BaseModel):
    manager_id: int
    manager_name: str
    total_leads: int
    active_leads: int
    closed_leads: int
    total_messages: int


class DailyStats(BaseModel):
    date: date
    new_leads: int
    closed_leads: int
    messages_count: int


class Last24HoursStats(BaseModel):
    new_leads: int
    closed_leads: int
    messages_count: int
    active_conversations: int


class ManagerLast24HoursStats(BaseModel):
    manager_id: int
    manager_name: str
    new_leads: int
    closed_leads: int
    messages_count: int


class DailyManagerStats(BaseModel):
    date: date
    manager_id: int
    manager_name: str
    new_leads: int
    closed_leads: int
    messages_count: int


@router.get("/overview", response_model=OverviewStats)
async def get_overview_stats(
        current_user: User = Depends(require_manager),
        db: Session = Depends(get_db)
):
    query = db.query(Lead)

    if current_user.role == "manager":
        query = query.filter(Lead.assigned_manager_id == current_user.id)

    total_leads = query.count()
    active_leads = query.filter(Lead.status != "closed").count()
    closed_leads = query.filter(Lead.status == "closed").count()

    lead_ids = [lead.id for lead in query.all()]
    total_messages = db.query(Message).filter(
        Message.lead_id.in_(lead_ids)).count() if lead_ids else 0

    managers_count = db.query(User).filter(
        User.role == "manager",
        User.is_active == True
    ).count()

    return {
        "total_leads": total_leads,
        "active_leads": active_leads,
        "closed_leads": closed_leads,
        "total_messages": total_messages,
        "managers_count": managers_count
    }


@router.get("/managers", response_model=List[ManagerStats])
async def get_all_managers_stats(
        current_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    """Статистика по всем менеджерам (только для админа)"""
    managers = db.query(User).filter(
        User.role == "manager",
        User.is_active == True
    ).all()

    result = []
    for manager in managers:
        leads = db.query(Lead).filter(
            Lead.assigned_manager_id == manager.id).all()

        total_leads = len(leads)
        active_leads = sum(1 for lead in leads if lead.status != "closed")
        closed_leads = sum(1 for lead in leads if lead.status == "closed")

        lead_ids = [lead.id for lead in leads]
        total_messages = db.query(Message).filter(
            Message.lead_id.in_(lead_ids)).count() if lead_ids else 0

        result.append({
            "manager_id": manager.id,
            "manager_name": manager.full_name,
            "total_leads": total_leads,
            "active_leads": active_leads,
            "closed_leads": closed_leads,
            "total_messages": total_messages
        })

    return result


@router.get("/manager/{manager_id}", response_model=ManagerStats)
async def get_manager_stats(
        manager_id: int,
        current_user: User = Depends(require_manager),
        db: Session = Depends(get_db)
):
    if current_user.role == "manager" and current_user.id != manager_id:
        raise HTTPException(status_code=403, detail="Access denied")

    manager = db.query(User).filter(
        User.id == manager_id,
        User.role == "manager"
    ).first()
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")

    leads = db.query(Lead).filter(Lead.assigned_manager_id == manager.id).all()

    total_leads = len(leads)
    active_leads = sum(1 for lead in leads if lead.status != "closed")
    closed_leads = sum(1 for lead in leads if lead.status == "closed")

    lead_ids = [lead.id for lead in leads]
    total_messages = db.query(Message).filter(
        Message.lead_id.in_(lead_ids)).count() if lead_ids else 0

    return {
        "manager_id": manager.id,
        "manager_name": manager.full_name,
        "total_leads": total_leads,
        "active_leads": active_leads,
        "closed_leads": closed_leads,
        "total_messages": total_messages
    }


@router.get("/daily", response_model=List[DailyStats])
async def get_daily_stats(
        days: int = 7,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        current_user: User = Depends(require_manager),
        db: Session = Depends(get_db)
):
    """
    Общая статистика по дням

    Параметры:
    - days: количество дней от сегодня (если не указаны даты)
    - start_date: начальная дата (формат: YYYY-MM-DD)
    - end_date: конечная дата (формат: YYYY-MM-DD)
    """
    # Определяем диапазон дат
    if not end_date:
        end_date = datetime.utcnow().date()
    if not start_date:
        start_date = end_date - timedelta(days=days - 1)

    query = db.query(Lead)

    if current_user.role == "manager":
        query = query.filter(Lead.assigned_manager_id == current_user.id)

    leads = query.all()

    stats_dict = {}

    for lead in leads:
        lead_date = lead.created_at.date()
        if start_date <= lead_date <= end_date:
            if lead_date not in stats_dict:
                stats_dict[lead_date] = {
                    "new_leads": 0,
                    "closed_leads": 0,
                    "messages_count": 0
                }
            stats_dict[lead_date]["new_leads"] += 1

        if lead.closed_at:
            closed_date = lead.closed_at.date()
            if start_date <= closed_date <= end_date:
                if closed_date not in stats_dict:
                    stats_dict[closed_date] = {
                        "new_leads": 0,
                        "closed_leads": 0,
                        "messages_count": 0
                    }
                stats_dict[closed_date]["closed_leads"] += 1

    lead_ids = [lead.id for lead in leads]
    if lead_ids:
        messages = db.query(Message).filter(
            Message.lead_id.in_(lead_ids)).all()
        for msg in messages:
            msg_date = msg.created_at.date()
            if start_date <= msg_date <= end_date:
                if msg_date not in stats_dict:
                    stats_dict[msg_date] = {
                        "new_leads": 0,
                        "closed_leads": 0,
                        "messages_count": 0
                    }
                stats_dict[msg_date]["messages_count"] += 1

    result = [
        {
            "date": date_key,
            "new_leads": values["new_leads"],
            "closed_leads": values["closed_leads"],
            "messages_count": values["messages_count"]
        }
        for date_key, values in sorted(stats_dict.items(), reverse=True)
    ]

    return result


@router.get("/daily/managers", response_model=List[DailyManagerStats])
async def get_daily_managers_stats(
        days: int = 7,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        manager_id: Optional[int] = None,
        current_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    """
    Статистика по дням с разбивкой по менеджерам (только для админа)

    Параметры:
    - days: количество дней от сегодня (если не указаны даты)
    - start_date: начальная дата (формат: YYYY-MM-DD)
    - end_date: конечная дата (формат: YYYY-MM-DD)
    - manager_id: ID конкретного менеджера (опционально, для фильтрации)

    Примеры использования:
    - /stats/daily/managers?days=7 - последние 7 дней, все менеджеры
    - /stats/daily/managers?start_date=2025-10-20&end_date=2025-10-26 - конкретный период
    - /stats/daily/managers?start_date=2025-10-26&end_date=2025-10-26 - один конкретный день
    - /stats/daily/managers?manager_id=5&days=30 - конкретный менеджер за 30 дней
    - /stats/daily/managers?manager_id=5&start_date=2025-10-01&end_date=2025-10-26 - менеджер за период
    """
    # Определяем диапазон дат
    if not end_date:
        end_date = datetime.utcnow().date()
    if not start_date:
        start_date = end_date - timedelta(days=days - 1)

    # Фильтр менеджеров
    managers_query = db.query(User).filter(
        User.role == "manager",
        User.is_active == True
    )

    if manager_id:
        managers_query = managers_query.filter(User.id == manager_id)

    managers = managers_query.all()

    if not managers:
        return []

    result = []

    for manager in managers:
        leads = db.query(Lead).filter(
            Lead.assigned_manager_id == manager.id
        ).all()

        stats_dict = {}

        # Новые лиды по дням
        for lead in leads:
            lead_date = lead.created_at.date()
            if start_date <= lead_date <= end_date:
                if lead_date not in stats_dict:
                    stats_dict[lead_date] = {
                        "new_leads": 0,
                        "closed_leads": 0,
                        "messages_count": 0
                    }
                stats_dict[lead_date]["new_leads"] += 1

            # Закрытые лиды по дням
            if lead.closed_at:
                closed_date = lead.closed_at.date()
                if start_date <= closed_date <= end_date:
                    if closed_date not in stats_dict:
                        stats_dict[closed_date] = {
                            "new_leads": 0,
                            "closed_leads": 0,
                            "messages_count": 0
                        }
                    stats_dict[closed_date]["closed_leads"] += 1

        # Сообщения по дням
        lead_ids = [lead.id for lead in leads]
        if lead_ids:
            messages = db.query(Message).filter(
                Message.lead_id.in_(lead_ids)
            ).all()
            for msg in messages:
                msg_date = msg.created_at.date()
                if start_date <= msg_date <= end_date:
                    if msg_date not in stats_dict:
                        stats_dict[msg_date] = {
                            "new_leads": 0,
                            "closed_leads": 0,
                            "messages_count": 0
                        }
                    stats_dict[msg_date]["messages_count"] += 1

        # Формируем результат
        for date_key, values in stats_dict.items():
            result.append({
                "date": date_key,
                "manager_id": manager.id,
                "manager_name": manager.full_name,
                "new_leads": values["new_leads"],
                "closed_leads": values["closed_leads"],
                "messages_count": values["messages_count"]
            })

    # Сортируем по дате (новые сверху), потом по менеджеру
    result.sort(key=lambda x: (x["date"], x["manager_name"]), reverse=True)

    return result


@router.get("/last24hours", response_model=Last24HoursStats)
async def get_last_24_hours_stats(
        current_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    """Статистика за последние 24 часа (только для админа)"""
    time_24h_ago = datetime.utcnow() - timedelta(hours=24)

    new_leads = db.query(Lead).filter(Lead.created_at >= time_24h_ago).count()

    closed_leads = db.query(Lead).filter(
        Lead.closed_at >= time_24h_ago,
        Lead.closed_at.isnot(None)
    ).count()

    messages_count = db.query(Message).filter(
        Message.created_at >= time_24h_ago
    ).count()

    active_conversations = db.query(Lead).filter(
        Lead.last_updated_at >= time_24h_ago,
        Lead.status != "closed"
    ).count()

    return {
        "new_leads": new_leads,
        "closed_leads": closed_leads,
        "messages_count": messages_count,
        "active_conversations": active_conversations
    }


@router.get("/last24hours/managers",
            response_model=List[ManagerLast24HoursStats])
async def get_last_24_hours_managers_stats(
        current_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    """Статистика за последние 24 часа по менеджерам (только для админа)"""
    time_24h_ago = datetime.utcnow() - timedelta(hours=24)

    managers = db.query(User).filter(
        User.role == "manager",
        User.is_active == True
    ).all()

    result = []
    for manager in managers:
        new_leads = db.query(Lead).filter(
            Lead.assigned_manager_id == manager.id,
            Lead.created_at >= time_24h_ago
        ).count()

        closed_leads = db.query(Lead).filter(
            Lead.assigned_manager_id == manager.id,
            Lead.closed_at >= time_24h_ago,
            Lead.closed_at.isnot(None)
        ).count()

        lead_ids = [lead.id for lead in db.query(Lead).filter(
            Lead.assigned_manager_id == manager.id
        ).all()]

        messages_count = 0
        if lead_ids:
            messages_count = db.query(Message).filter(
                Message.lead_id.in_(lead_ids),
                Message.created_at >= time_24h_ago
            ).count()

        result.append({
            "manager_id": manager.id,
            "manager_name": manager.full_name,
            "new_leads": new_leads,
            "closed_leads": closed_leads,
            "messages_count": messages_count
        })

    return result