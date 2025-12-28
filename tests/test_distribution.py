# tests/test_distribution.py

import pytest
from backend.app.models import User, Project
from backend.app.distribution import get_next_manager
from backend.app.auth import get_password_hash


def test_round_robin(db_session):
    project = Project(name="p1")
    m1 = User(username="m1", password_hash=get_password_hash("p"),
              role="manager", full_name="M1", is_active=True)
    m2 = User(username="m2", password_hash=get_password_hash("p"),
              role="manager", full_name="M2", is_active=True)

    db_session.add_all([m1, m2, project])
    db_session.flush()

    project.managers.extend([m1, m2])
    db_session.commit()

    r1 = get_next_manager(db_session, project.id)
    r2 = get_next_manager(db_session, project.id)
    r3 = get_next_manager(db_session, project.id)
    r4 = get_next_manager(db_session, project.id)

    assert r1.username == "m1"
    assert r2.username == "m2"
    assert r3.username == "m1"
    assert r4.username == "m2"


def test_no_managers(db_session):
    project = Project(name="empty")
    db_session.add(project)
    db_session.commit()

    with pytest.raises(ValueError):
        get_next_manager(db_session, project.id)


def test_only_active(db_session):
    project = Project(name="p1")
    active = User(username="active", password_hash=get_password_hash("p"),
                  role="manager", full_name="A", is_active=True)
    inactive = User(username="inactive", password_hash=get_password_hash("p"),
                    role="manager", full_name="I", is_active=False)

    db_session.add_all([active, inactive, project])
    db_session.flush()

    project.managers.extend([active, inactive])
    db_session.commit()

    for i in range(3):
        manager = get_next_manager(db_session, project.id)
        assert manager.username == "active"