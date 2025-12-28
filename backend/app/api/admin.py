# backend/app/api/admin.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from datetime import datetime
from ..database import get_db
from ..models import User, Bot, Project, Lead
from ..auth import require_admin, get_password_hash
from ..telegram_handler import set_telegram_webhook

router = APIRouter(prefix="/admin")


# ========== MODELS ==========

class ManagerInfo(BaseModel):
    id: int
    username: str
    full_name: str

    class Config:
        from_attributes = True


class ProjectInfo(BaseModel):
    id: int
    name: str


class ManagerResponse(BaseModel):
    id: int
    username: str
    role: str
    full_name: str
    is_active: bool
    created_at: datetime
    projects: List[ProjectInfo] = []

    class Config:
        from_attributes = True


class ManagerCreate(BaseModel):
    username: str
    password: str
    full_name: str


class ManagerUpdate(BaseModel):
    password: str | None = None
    full_name: str | None = None
    is_active: bool | None = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectWithManagersResponse(ProjectResponse):
    managers: List[ManagerInfo]


class ProjectCreate(BaseModel):
    name: str


class AddManagersRequest(BaseModel):
    manager_ids: List[int]


class BotResponse(BaseModel):
    id: int
    identifier: str
    name: str
    project_id: int
    token: str
    auto_reply: str
    webhook_url: str | None
    is_active: bool

    class Config:
        from_attributes = True


class BotCreate(BaseModel):
    identifier: str
    name: str
    token: str
    auto_reply: str


class BotUpdate(BaseModel):
    identifier: str | None = None
    name: str | None = None
    token: str | None = None
    auto_reply: str | None = None
    is_active: bool | None = None


# ========== MANAGERS ==========

@router.get(
    "/managers",
    response_model=List[ManagerResponse],
    tags=["Admin - Managers"],
    summary="Получить список менеджеров",
    description="Возвращает список всех пользователей с их проектами"
)
async def get_managers(
        current_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    users = db.query(User).order_by(User.id).all()

    result = []
    for user in users:
        user_projects = []
        if user.role == "manager":
            user_projects = [{"id": p.id, "name": p.name} for p in user.projects]

        result.append({
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "created_at": user.created_at,
            "projects": user_projects
        })

    return result


@router.post(
    "/managers",
    response_model=ManagerResponse,
    tags=["Admin - Managers"],
    summary="Создать менеджера",
    description="Создает нового менеджера в системе"
)
async def create_manager(
        manager_data: ManagerCreate,
        current_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.username == manager_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        username=manager_data.username,
        password_hash=get_password_hash(manager_data.password),
        role="manager",
        full_name=manager_data.full_name,
        is_active=True,
        created_at=datetime.utcnow()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "id": new_user.id,
        "username": new_user.username,
        "role": new_user.role,
        "full_name": new_user.full_name,
        "is_active": new_user.is_active,
        "created_at": new_user.created_at,
        "projects": []
    }


@router.put(
    "/managers/{manager_id}",
    response_model=ManagerResponse,
    tags=["Admin - Managers"],
    summary="Обновить менеджера",
    description="Обновляет данные менеджера (пароль, имя, статус активности)"
)
async def update_manager(
        manager_id: int,
        manager_data: ManagerUpdate,
        current_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == manager_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Manager not found")

    if manager_data.password:
        user.password_hash = get_password_hash(manager_data.password)

    if manager_data.full_name:
        user.full_name = manager_data.full_name

    if manager_data.is_active is not None:
        user.is_active = manager_data.is_active

    db.commit()
    db.refresh(user)

    user_projects = []
    if user.role == "manager":
        user_projects = [{"id": p.id, "name": p.name} for p in user.projects]

    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "created_at": user.created_at,
        "projects": user_projects
    }


@router.delete(
    "/managers/{manager_id}",
    tags=["Admin - Managers"],
    summary="Удалить менеджера",
    description="Удаляет менеджера из системы"
)
async def delete_manager(
        manager_id: int,
        current_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == manager_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Manager not found")

    db.delete(user)
    db.commit()

    return {"status": "deleted", "manager_id": manager_id}


# ========== PROJECTS ==========

@router.get(
    "/projects",
    response_model=List[ProjectResponse],
    tags=["Admin - Projects"],
    summary="Получить список проектов",
    description="Возвращает список всех проектов"
)
async def get_projects(
        current_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    projects = db.query(Project).order_by(Project.id).all()
    return projects


@router.get(
    "/projects/{project_id}",
    response_model=ProjectWithManagersResponse,
    tags=["Admin - Projects"],
    summary="Получить детали проекта",
    description="Возвращает проект с назначенными менеджерами"
)
async def get_project(
        project_id: int,
        current_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "id": project.id,
        "name": project.name,
        "created_at": project.created_at,
        "managers": [
            {"id": m.id, "username": m.username, "full_name": m.full_name}
            for m in project.managers
        ]
    }


@router.post(
    "/projects",
    response_model=ProjectResponse,
    tags=["Admin - Projects"],
    summary="Создать проект",
    description="Создает новый проект"
)
async def create_project(
        project_data: ProjectCreate,
        current_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    existing = db.query(Project).filter(Project.name == project_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Project already exists")

    new_project = Project(name=project_data.name, created_at=datetime.utcnow())
    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return new_project


@router.put(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    tags=["Admin - Projects"],
    summary="Обновить проект",
    description="Обновляет название проекта"
)
async def update_project(
        project_id: int,
        project_data: ProjectCreate,
        current_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    existing = db.query(Project).filter(
        Project.name == project_data.name,
        Project.id != project_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Project name already exists")

    project.name = project_data.name
    db.commit()
    db.refresh(project)

    return project


@router.delete(
    "/projects/{project_id}",
    tags=["Admin - Projects"],
    summary="Удалить проект",
    description="Удаляет проект и всех связанных ботов"
)
async def delete_project(
        project_id: int,
        current_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()

    return {"status": "deleted", "project_id": project_id}


@router.post(
    "/projects/{project_id}/managers",
    tags=["Admin - Projects"],
    summary="Назначить менеджеров на проект",
    description="Добавляет менеджеров в проект (many-to-many)"
)
async def add_managers_to_project(
        project_id: int,
        data: AddManagersRequest,
        current_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    for manager_id in data.manager_ids:
        manager = db.query(User).filter(
            User.id == manager_id,
            User.role == "manager"
        ).first()
        if not manager:
            raise HTTPException(status_code=404, detail=f"Manager {manager_id} not found")

        if manager not in project.managers:
            project.managers.append(manager)

    db.commit()

    return {"status": "managers_added", "project_id": project_id}


@router.delete(
    "/projects/{project_id}/managers/{manager_id}",
    tags=["Admin - Projects"],
    summary="Убрать менеджера из проекта",
    description="Удаляет назначение менеджера на проект"
)
async def remove_manager_from_project(
        project_id: int,
        manager_id: int,
        current_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    manager = db.query(User).filter(User.id == manager_id).first()
    if not manager or manager not in project.managers:
        raise HTTPException(status_code=404, detail="Manager not in project")

    project.managers.remove(manager)
    db.commit()

    return {"status": "manager_removed", "project_id": project_id, "manager_id": manager_id}


# ========== BOTS ==========

@router.get(
    "/projects/{project_id}/bots",
    response_model=List[BotResponse],
    tags=["Admin - Bots"],
    summary="Получить ботов проекта",
    description="Возвращает всех ботов привязанных к проекту"
)
async def get_project_bots(
        project_id: int,
        current_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    bots = db.query(Bot).filter(Bot.project_id == project_id).all()
    return bots


@router.post(
    "/projects/{project_id}/bots",
    response_model=BotResponse,
    tags=["Admin - Bots"],
    summary="Создать бота",
    description="Создает нового Telegram бота для проекта и устанавливает webhook"
)
async def create_bot(
        project_id: int,
        bot_data: BotCreate,
        current_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    existing = db.query(Bot).filter(Bot.identifier == bot_data.identifier).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bot identifier already exists")

    new_bot = Bot(
        identifier=bot_data.identifier,
        name=bot_data.name,
        project_id=project_id,
        token=bot_data.token,
        auto_reply=bot_data.auto_reply,
        is_active=True
    )

    db.add(new_bot)
    db.commit()
    db.refresh(new_bot)

    webhook_success = await set_telegram_webhook(new_bot.token, new_bot.identifier)
    if webhook_success:
        from ..config import settings
        new_bot.webhook_url = f"{settings.BASE_URL}/webhook/{new_bot.identifier}"
        db.commit()
        db.refresh(new_bot)

    return new_bot


@router.put(
    "/projects/{project_id}/bots/{bot_id}",
    response_model=BotResponse,
    tags=["Admin - Bots"],
    summary="Обновить бота",
    description="Обновляет настройки бота и переустанавливает webhook если изменился токен"
)
async def update_bot(
        project_id: int,
        bot_id: int,
        bot_data: BotUpdate,
        current_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    bot = db.query(Bot).filter(
        Bot.id == bot_id,
        Bot.project_id == project_id
    ).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    webhook_needs_update = False

    if bot_data.identifier:
        existing = db.query(Bot).filter(
            Bot.identifier == bot_data.identifier,
            Bot.id != bot_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Bot identifier already exists")
        bot.identifier = bot_data.identifier
        webhook_needs_update = True

    if bot_data.name:
        bot.name = bot_data.name

    if bot_data.token:
        bot.token = bot_data.token
        webhook_needs_update = True

    if bot_data.auto_reply:
        bot.auto_reply = bot_data.auto_reply

    if bot_data.is_active is not None:
        bot.is_active = bot_data.is_active

    db.commit()
    db.refresh(bot)

    if webhook_needs_update:
        webhook_success = await set_telegram_webhook(bot.token, bot.identifier)
        if webhook_success:
            from ..config import settings
            bot.webhook_url = f"{settings.BASE_URL}/webhook/{bot.identifier}"
            db.commit()
            db.refresh(bot)

    return bot


@router.delete(
    "/projects/{project_id}/bots/{bot_id}",
    tags=["Admin - Bots"],
    summary="Удалить бота",
    description="Удаляет бота из проекта (только если нет связанных лидов)"
)
async def delete_bot(
        project_id: int,
        bot_id: int,
        current_user: User = Depends(require_admin),
        db: Session = Depends(get_db)
):
    bot = db.query(Bot).filter(
        Bot.id == bot_id,
        Bot.project_id == project_id
    ).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    leads_count = db.query(Lead).filter(Lead.bot_id == bot_id).count()
    if leads_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete bot: {leads_count} leads are associated with this bot"
        )

    db.delete(bot)
    db.commit()

    return {"status": "deleted", "bot_id": bot_id}