# tests/test_api_auth.py

import pytest


def test_login_success(client, admin_user):
    """Успешный логин"""
    response = client.post("/auth/login", data={
        "username": "admin",
        "password": "admin123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "admin"
    assert data["user"]["role"] == "admin"


def test_login_wrong_password(client, admin_user):
    """Неправильный пароль"""
    response = client.post("/auth/login", data={
        "username": "admin",
        "password": "wrong"
    })
    assert response.status_code == 401


def test_login_user_not_found(client):
    """Пользователь не существует"""
    response = client.post("/auth/login", data={
        "username": "notexist",
        "password": "pass"
    })
    assert response.status_code == 401


def test_get_current_user(client, admin_token):
    """Получение текущего пользователя"""
    response = client.get("/auth/me", headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert data["role"] == "admin"


def test_get_current_user_no_token(client):
    """Доступ без токена"""
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_get_current_user_invalid_token(client):
    """Неправильный токен"""
    response = client.get("/auth/me", headers={
        "Authorization": "Bearer invalidtoken"
    })
    assert response.status_code == 401