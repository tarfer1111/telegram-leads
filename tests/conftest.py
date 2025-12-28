# tests/conftest.py

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from backend.app.models import Base, User, Project, Bot
from backend.app.auth import get_password_hash
from backend.app.main import app

TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(TEST_DATABASE_URL,
                           connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
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
    p = Project(name="Project 1")
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


@pytest.fixture(scope="function")
def project2(db_session):
    p = Project(name="Project 2")
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


@pytest.fixture(scope="function")
def bot1(db_session, project1):
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
    response = client.post("/auth/login", data={
        "username": "admin",
        "password": "admin123"
    })
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def manager1_token(client, manager1):
    response = client.post("/auth/login", data={
        "username": "manager1",
        "password": "pass123"
    })
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def manager2_token(client, manager2):
    response = client.post("/auth/login", data={
        "username": "manager2",
        "password": "pass123"
    })
    return response.json()["access_token"]