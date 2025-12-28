# tests/test_api_fixtures.py

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models import User, Project, Bot, Lead
from backend.app.auth import get_password_hash


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI test client"""
    from backend.app.database import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def admin_user(db_session):
    """Админ пользователь"""
    admin = User(
        username="admin",
        password_hash=get_password_hash("admin123"),
        role="admin",
        full_name="Admin User",
        is_active=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture(scope="function")
def manager1(db_session):
    """Менеджер 1"""
    m = User(
        username="manager1",
        password_hash=get_password_hash("pass123"),
        role="manager",
        full_name="Manager One",
        is_active=True
    )
    db_session.add(m)
    db_session.commit()
    db_session.refresh(m)
    return m


@pytest.fixture(scope="function")
def manager2(db_session):
    """Менеджер 2"""
    m = User(
        username="manager2",
        password_hash=get_password_hash("pass123"),
        role="manager",
        full_name="Manager Two",
        is_active=True
    )
    db_session.add(m)
    db_session.commit()
    db_session.refresh(m)
    return m


@pytest.fixture(scope="function")
def project1(db_session):
    """Проект 1"""
    p = Project(name="Project 1")
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


@pytest.fixture(scope="function")
def project2(db_session):
    """Проект 2"""
    p = Project(name="Project 2")
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


@pytest.fixture(scope="function")
def bot1(db_session, project1):
    """Бот для проекта 1"""
    b = Bot(
        identifier="bot1",
        name="Bot 1",
        project_id=project1.id,
        token="token1",
        auto_reply="Hello",
        is_active=True
    )
    db_session.add(b)
    db_session.commit()
    db_session.refresh(b)
    return b


@pytest.fixture(scope="function")
def admin_token(client, admin_user):
    """Токен админа"""
    response = client.post("/auth/login", data={
        "username": "admin",
        "password": "admin123"
    })
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def manager1_token(client, manager1):
    """Токен менеджера 1"""
    response = client.post("/auth/login", data={
        "username": "manager1",
        "password": "pass123"
    })
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def manager2_token(client, manager2):
    """Токен менеджера 2"""
    response = client.post("/auth/login", data={
        "username": "manager2",
        "password": "pass123"
    })
    return response.json()["access_token"]