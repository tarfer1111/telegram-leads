# backend/app/api/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from ..database import get_db
from ..models import User
from ..auth import verify_password, create_access_token, get_current_active_user

router = APIRouter(prefix="/auth", tags=["auth"])


class ProjectInfo(BaseModel):
    id: int
    name: str


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    full_name: str
    is_active: bool
    projects: List[ProjectInfo] = []

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


@router.post("/login", response_model=LoginResponse)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):
    """Авторизация (для всех ролей)"""
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive"
        )

    access_token = create_access_token(data={"sub": user.username})

    user_projects = []
    if user.role == "manager":
        user_projects = [{"id": p.id, "name": p.name} for p in user.projects]

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "projects": user_projects
        }
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Получить информацию о текущем пользователе"""
    user_projects = []
    if current_user.role == "manager":
        user_projects = [{"id": p.id, "name": p.name} for p in current_user.projects]

    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "projects": user_projects
    }