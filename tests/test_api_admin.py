# tests/test_api_admin.py

import pytest


# ========== MANAGERS ==========

def test_get_managers(client, admin_token, manager1, manager2):
    """Получение списка менеджеров"""
    response = client.get("/admin/managers", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3  # admin + 2 managers


def test_create_manager(client, admin_token):
    """Создание менеджера"""
    response = client.post("/admin/managers",
                           headers={"Authorization": f"Bearer {admin_token}"},
                           json={
                               "username": "newmanager",
                               "password": "pass123",
                               "full_name": "New Manager"
                           }
                           )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newmanager"
    assert data["role"] == "manager"


def test_create_manager_duplicate(client, admin_token, manager1):
    """Дубликат username"""
    response = client.post("/admin/managers",
                           headers={"Authorization": f"Bearer {admin_token}"},
                           json={
                               "username": "manager1",
                               "password": "pass",
                               "full_name": "Test"
                           }
                           )
    assert response.status_code == 400


def test_update_manager(client, admin_token, manager1):
    """Обновление менеджера"""
    response = client.put(f"/admin/managers/{manager1.id}",
                          headers={"Authorization": f"Bearer {admin_token}"},
                          json={"full_name": "Updated Name"}
                          )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"


def test_delete_manager(client, admin_token, manager1):
    """Удаление менеджера"""
    response = client.delete(f"/admin/managers/{manager1.id}",
                             headers={"Authorization": f"Bearer {admin_token}"}
                             )
    assert response.status_code == 200


def test_manager_access_denied(client, manager1_token):
    """Менеджер не может управлять менеджерами"""
    response = client.get("/admin/managers", headers={
        "Authorization": f"Bearer {manager1_token}"
    })
    assert response.status_code == 403


# ========== PROJECTS ==========

def test_get_projects(client, admin_token, project1, project2):
    """Получение списка проектов"""
    response = client.get("/admin/projects", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_create_project(client, admin_token):
    """Создание проекта"""
    response = client.post("/admin/projects",
                           headers={"Authorization": f"Bearer {admin_token}"},
                           json={"name": "New Project"}
                           )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Project"


def test_create_project_duplicate(client, admin_token, project1):
    """Дубликат имени проекта"""
    response = client.post("/admin/projects",
                           headers={"Authorization": f"Bearer {admin_token}"},
                           json={"name": "Project 1"}
                           )
    assert response.status_code == 400


def test_get_project_details(client, admin_token, project1, manager1,
                             db_session):
    """Детали проекта с менеджерами"""
    project1.managers.append(manager1)
    db_session.commit()

    response = client.get(f"/admin/projects/{project1.id}", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Project 1"
    assert len(data["managers"]) == 1
    assert data["managers"][0]["username"] == "manager1"


def test_add_managers_to_project(client, admin_token, project1, manager1,
                                 manager2):
    """Добавление менеджеров в проект"""
    response = client.post(f"/admin/projects/{project1.id}/managers",
                           headers={"Authorization": f"Bearer {admin_token}"},
                           json={"manager_ids": [manager1.id, manager2.id]}
                           )
    assert response.status_code == 200


def test_remove_manager_from_project(client, admin_token, project1, manager1,
                                     db_session):
    """Удаление менеджера из проекта"""
    project1.managers.append(manager1)
    db_session.commit()

    response = client.delete(
        f"/admin/projects/{project1.id}/managers/{manager1.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
        )
    assert response.status_code == 200


def test_delete_project(client, admin_token, project1):
    """Удаление проекта"""
    response = client.delete(f"/admin/projects/{project1.id}",
                             headers={"Authorization": f"Bearer {admin_token}"}
                             )
    assert response.status_code == 200


# ========== BOTS ==========

def test_get_project_bots(client, admin_token, project1, bot1):
    """Получение ботов проекта"""
    response = client.get(f"/admin/projects/{project1.id}/bots",
                          headers={"Authorization": f"Bearer {admin_token}"}
                          )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_delete_bot(client, admin_token, project1, bot1):
    """Удаление бота"""
    response = client.delete(f"/admin/projects/{project1.id}/bots/{bot1.id}",
                             headers={"Authorization": f"Bearer {admin_token}"}
                             )
    assert response.status_code == 200