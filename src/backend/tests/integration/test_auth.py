"""Tests for authentication endpoints."""

import uuid

import pytest
from httpx import AsyncClient
from jose import jwt

from app.config import settings

def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}

pytestmark = pytest.mark.asyncio


async def test_register_success(client: AsyncClient):
    email = f"newuser_{uuid.uuid4().hex[:8]}@test.com"
    resp = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "SecurePass123",
        "full_name": "New User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == email
    assert data["full_name"] == "New User"
    assert "id" in data


async def test_register_duplicate_email(client: AsyncClient, test_user):
    _, email, _ = test_user
    resp = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "SecurePass123",
        "full_name": "Duplicate User",
    })
    assert resp.status_code == 409
    assert "already registered" in resp.json()["detail"].lower()


async def test_register_short_password(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "email": f"shortpw_{uuid.uuid4().hex[:8]}@test.com",
        "password": "short",
        "full_name": "Short PW User",
    })
    assert resp.status_code == 422


async def test_register_invalid_email(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "not-an-email",
        "password": "SecurePass123",
        "full_name": "Bad Email User",
    })
    assert resp.status_code == 422


async def test_login_success(client: AsyncClient, test_user):
    _, email, password = test_user
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(client: AsyncClient, test_user):
    _, email, _ = test_user
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPass999"})
    assert resp.status_code == 401


async def test_login_nonexistent_email(client: AsyncClient):
    resp = await client.post("/api/v1/auth/login", json={
        "email": "nonexistent@test.com",
        "password": "SomePass123",
    })
    assert resp.status_code == 401


async def test_jwt_contains_correct_claims(client: AsyncClient, test_user):
    user_id, email, password = test_user
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == user_id
    assert payload["user_type"] == "user"
    assert payload["type"] == "access"
    assert "jti" in payload
    assert "exp" in payload


async def test_logout_revokes_token(client: AsyncClient, user_token: str):
    # Logout
    resp = await client.post("/api/v1/auth/logout", headers=auth_header(user_token))
    assert resp.status_code == 204

    # Token should be revoked now — access protected route
    resp = await client.get("/api/v1/applications/stats", headers=auth_header(user_token))
    assert resp.status_code == 401


async def test_refresh_token(client: AsyncClient, test_user):
    _, email, password = test_user
    login_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    refresh_token = login_resp.json()["refresh_token"]

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["access_token"] != login_resp.json()["access_token"]


async def test_refresh_with_access_token_fails(client: AsyncClient, user_token: str):
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": user_token})
    assert resp.status_code == 401


async def test_forgot_password_always_200(client: AsyncClient):
    # Existing email
    resp = await client.post("/api/v1/auth/forgot-password", json={"email": "nonexistent@test.com"})
    assert resp.status_code == 200
    assert "reset link" in resp.json()["message"].lower()


async def test_reset_password_invalid_token(client: AsyncClient):
    resp = await client.post("/api/v1/auth/reset-password", json={
        "token": "invalid-token",
        "new_password": "NewSecure123",
    })
    assert resp.status_code == 400


async def test_csrf_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/csrf-token")
    assert resp.status_code == 200
    assert "csrf_token" in resp.json()


# --- Admin Auth ---

async def test_admin_login_success(client: AsyncClient, test_admin):
    _, email, password = test_admin
    resp = await client.post("/api/v1/auth/admin/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data

    # Verify admin claims
    payload = jwt.decode(data["access_token"], settings.JWT_SECRET_KEY, algorithms=["HS256"])
    assert payload["user_type"] == "admin"
    assert payload["role"] == "admin"


async def test_admin_login_wrong_password(client: AsyncClient, test_admin):
    _, email, _ = test_admin
    resp = await client.post("/api/v1/auth/admin/login", json={"email": email, "password": "Wrong123"})
    assert resp.status_code == 401


async def test_admin_logout(client: AsyncClient, admin_token: str):
    resp = await client.post("/api/v1/auth/admin/logout", headers=auth_header(admin_token))
    assert resp.status_code == 204


async def test_user_token_cannot_access_admin(client: AsyncClient, user_token: str):
    resp = await client.get("/api/v1/admin/stats", headers=auth_header(user_token))
    assert resp.status_code == 403
