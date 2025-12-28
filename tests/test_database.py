# tests/test_database.py

import pytest
from backend.app.models import User, Project, Bot, Lead, Message
from backend.app.auth import get_password_hash


def test_create_user(db_session):
    user = User(
        username="test_user",
        password_hash=get_password_hash("password123"),
        role="manager",
        full_name="Test User",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    found = db_session.query(User).filter(User.username == "test_user").first()
    assert found is not None
    assert found.role == "manager"


def test_create_project(db_session):
    project = Project(name="test_project")
    db_session.add(project)
    db_session.commit()

    found = db_session.query(Project).filter(
        Project.name == "test_project").first()
    assert found is not None


def test_project_managers(db_session):
    project = Project(name="project1")
    m1 = User(username="m1", password_hash=get_password_hash("p"),
              role="manager", full_name="M1")
    m2 = User(username="m2", password_hash=get_password_hash("p"),
              role="manager", full_name="M2")

    db_session.add_all([m1, m2, project])
    db_session.flush()

    project.managers.extend([m1, m2])
    db_session.commit()

    found = db_session.query(Project).filter(
        Project.name == "project1").first()
    assert len(found.managers) == 2


def test_create_bot(db_session):
    project = Project(name="p1")
    db_session.add(project)
    db_session.flush()

    bot = Bot(identifier="bot1", name="Bot", project_id=project.id,
              token="tok", auto_reply="Hi")
    db_session.add(bot)
    db_session.commit()

    found = db_session.query(Bot).filter(Bot.identifier == "bot1").first()
    assert found is not None


def test_create_lead(db_session):
    project = Project(name="p1")
    manager = User(username="m1", password_hash=get_password_hash("p"),
                   role="manager", full_name="M")
    bot = Bot(identifier="b1", name="B", project_id=None, token="t",
              auto_reply="H")

    db_session.add_all([project, manager])
    db_session.flush()

    bot.project_id = project.id
    db_session.add(bot)
    db_session.flush()

    lead = Lead(
        telegram_chat_id=123456,
        bot_id=bot.id,
        project_id=project.id,
        assigned_manager_id=manager.id,
        status="active"
    )
    db_session.add(lead)
    db_session.commit()

    found = db_session.query(Lead).filter(
        Lead.telegram_chat_id == 123456).first()
    assert found is not None


def test_lead_messages(db_session):
    project = Project(name="p1")
    manager = User(username="m1", password_hash=get_password_hash("p"),
                   role="manager", full_name="M")
    bot = Bot(identifier="b1", name="B", project_id=None, token="t",
              auto_reply="H")

    db_session.add_all([project, manager])
    db_session.flush()

    bot.project_id = project.id
    db_session.add(bot)
    db_session.flush()

    lead = Lead(telegram_chat_id=123, bot_id=bot.id, project_id=project.id,
                assigned_manager_id=manager.id)
    db_session.add(lead)
    db_session.flush()

    msg1 = Message(lead_id=lead.id, sender="lead", text="Hello")
    msg2 = Message(lead_id=lead.id, sender="manager", text="Hi")
    db_session.add_all([msg1, msg2])
    db_session.commit()

    found = db_session.query(Lead).filter(Lead.id == lead.id).first()
    assert len(found.messages) == 2