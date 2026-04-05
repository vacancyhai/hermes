"""Tests for authentication endpoints.

User auth is now Firebase-based (POST /verify-token).
Admin auth remains local bcrypt + JWT (POST /admin/login).
"""

import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from jose import jwt

from app.config import settings
from app.routers.auth import create_access_token, create_refresh_token


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


pytestmark = pytest.mark.asyncio


# ─── Firebase verify-token ───────────────────────────────────────────────────


async def test_verify_token_creates_new_user(client: AsyncClient):
    """verify-token creates a new user when firebase_uid not found."""
    decoded = {
        "uid": f"new-uid-{uuid.uuid4().hex[:8]}",
        "email": f"firebase_{uuid.uuid4().hex[:8]}@test.com",
        "email_verified": True,
        "name": "Firebase User",
        "firebase": {"sign_in_provider": "google.com"},
    }
    with patch("app.firebase.verify_id_token", return_value=decoded):
        resp = await client.post("/api/v1/auth/verify-token", json={"id_token": "fake-token"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


async def test_verify_token_finds_existing_user_by_uid(client: AsyncClient, test_user, db):
    """verify-token finds an existing user matched by firebase_uid."""
    from app.models.user import User
    from sqlalchemy import select

    user_id, email, _ = test_user
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one()
    existing_uid = user.firebase_uid  # set by fixture

    decoded = {
        "uid": existing_uid,
        "email": email,
        "email_verified": True,
        "firebase": {"sign_in_provider": "password"},
    }
    with patch("app.firebase.verify_id_token", return_value=decoded):
        resp = await client.post("/api/v1/auth/verify-token", json={"id_token": "fake-token"})
    assert resp.status_code == 200

    token = resp.json()["access_token"]
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == user_id


async def test_verify_token_migrates_legacy_user(client: AsyncClient, test_user, db):
    """verify-token links firebase_uid to a legacy user matched by email."""
    from app.models.user import User
    from sqlalchemy import select

    user_id, email, _ = test_user
    # Remove firebase_uid so the lookup falls through to email
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one()
    user.firebase_uid = None
    user.migration_status = "legacy"
    await db.commit()

    new_uid = f"migrated-uid-{uuid.uuid4().hex[:8]}"
    decoded = {
        "uid": new_uid,
        "email": email,
        "email_verified": True,
        "firebase": {"sign_in_provider": "password"},
    }
    with patch("app.firebase.verify_id_token", return_value=decoded):
        resp = await client.post("/api/v1/auth/verify-token", json={"id_token": "fake-token"})
    assert resp.status_code == 200

    await db.refresh(user)
    assert user.firebase_uid == new_uid
    assert user.migration_status == "migrated"


async def test_verify_token_invalid_token(client: AsyncClient):
    """Invalid Firebase token returns 401."""
    with patch("app.firebase.verify_id_token", side_effect=ValueError("Invalid token")):
        resp = await client.post("/api/v1/auth/verify-token", json={"id_token": "bad-token"})
    assert resp.status_code == 401


async def test_verify_token_phone_only_user(client: AsyncClient):
    """Phone-only Firebase user (no email) creates an account.

    Uses the Firebase test phone number configured in Firebase Console:
      Phone: +917777777777  OTP: 123456
    """
    decoded = {
        "uid": f"phone-uid-{uuid.uuid4().hex[:8]}",
        "phone_number": "+917777777777",  # Firebase test phone number
        "firebase": {"sign_in_provider": "phone"},
    }
    with patch("app.firebase.verify_id_token", return_value=decoded):
        resp = await client.post("/api/v1/auth/verify-token", json={"id_token": "fake-token"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data


async def test_verify_token_phone_user_stores_phone(client: AsyncClient, db):
    """Phone number from Firebase token is stored on the user record."""
    from app.models.user import User
    from sqlalchemy import select

    uid = f"phone-store-uid-{uuid.uuid4().hex[:8]}"
    decoded = {
        "uid": uid,
        "phone_number": "+917777777777",  # Firebase test phone number
        "firebase": {"sign_in_provider": "phone"},
    }
    with patch("app.firebase.verify_id_token", return_value=decoded):
        resp = await client.post("/api/v1/auth/verify-token", json={"id_token": "fake-token"})
    assert resp.status_code == 200

    from jose import jwt
    user_id = jwt.decode(resp.json()["access_token"], settings.JWT_SECRET_KEY, algorithms=["HS256"])["sub"]
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one()
    assert user.phone == "+917777777777"
    assert user.email is None  # phone-only, no email


async def test_verify_token_returns_correct_jwt_claims(client: AsyncClient):
    """Returned JWT contains correct user-type claims."""
    decoded = {
        "uid": f"claims-uid-{uuid.uuid4().hex[:8]}",
        "email": f"claims_{uuid.uuid4().hex[:8]}@test.com",
        "email_verified": True,
        "firebase": {"sign_in_provider": "password"},
    }
    with patch("app.firebase.verify_id_token", return_value=decoded):
        resp = await client.post("/api/v1/auth/verify-token", json={"id_token": "fake-token"})

    token = resp.json()["access_token"]
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
    assert payload["user_type"] == "user"
    assert payload["type"] == "access"
    assert "jti" in payload
    assert "exp" in payload


async def test_verify_token_suspended_user(client: AsyncClient, test_user, db):
    """Suspended user gets 403 on verify-token."""
    from app.models.user import User
    from sqlalchemy import select

    user_id, email, _ = test_user
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one()
    user.status = "suspended"
    await db.commit()

    decoded = {
        "uid": user.firebase_uid or f"uid-{uuid.uuid4().hex[:8]}",
        "email": email,
        "email_verified": True,
        "firebase": {"sign_in_provider": "password"},
    }
    with patch("app.firebase.verify_id_token", return_value=decoded):
        resp = await client.post("/api/v1/auth/verify-token", json={"id_token": "fake-token"})
    assert resp.status_code == 403


async def test_verify_token_deleted_user(client: AsyncClient, test_user, db):
    """Deleted user gets 401 on verify-token."""
    from app.models.user import User
    from sqlalchemy import select

    user_id, email, _ = test_user
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one()
    user.status = "deleted"
    await db.commit()

    decoded = {
        "uid": user.firebase_uid or f"uid-{uuid.uuid4().hex[:8]}",
        "email": email,
        "email_verified": True,
        "firebase": {"sign_in_provider": "password"},
    }
    with patch("app.firebase.verify_id_token", return_value=decoded):
        resp = await client.post("/api/v1/auth/verify-token", json={"id_token": "fake-token"})
    assert resp.status_code == 401


async def test_verify_token_full_name_from_body(client: AsyncClient):
    """full_name from request body is used when Firebase token has no name."""
    decoded = {
        "uid": f"noname-uid-{uuid.uuid4().hex[:8]}",
        "email": f"noname_{uuid.uuid4().hex[:8]}@test.com",
        "email_verified": False,
        "firebase": {"sign_in_provider": "password"},
    }
    with patch("app.firebase.verify_id_token", return_value=decoded):
        resp = await client.post("/api/v1/auth/verify-token", json={
            "id_token": "fake-token",
            "full_name": "Provided Name",
        })
    assert resp.status_code == 200


# ─── Logout & Refresh (user) ──────────────────────────────────────────────────


async def test_logout_revokes_token(client: AsyncClient, user_token: str):
    resp = await client.post("/api/v1/auth/logout", headers=auth_header(user_token))
    assert resp.status_code == 204

    # Token should be blocklisted — access protected route
    resp = await client.get("/api/v1/notifications", headers=auth_header(user_token))
    assert resp.status_code == 401


async def test_refresh_token(client: AsyncClient, test_user):
    user_id, _, _ = test_user
    refresh_token = create_refresh_token(user_id, "user")

    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["access_token"] != refresh_token


async def test_refresh_with_access_token_fails(client: AsyncClient, user_token: str):
    resp = await client.post("/api/v1/auth/refresh", json={"refresh_token": user_token})
    assert resp.status_code == 401


# ─── Admin Auth ───────────────────────────────────────────────────────────────


async def test_admin_login_success(client: AsyncClient, test_admin):
    _, email, password = test_admin
    resp = await client.post("/api/v1/auth/admin/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data

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


async def test_admin_refresh_token(client: AsyncClient, test_admin):
    _, email, password = test_admin
    login_resp = await client.post("/api/v1/auth/admin/login", json={"email": email, "password": password})
    refresh_token = login_resp.json()["refresh_token"]

    resp = await client.post("/api/v1/auth/admin/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_admin_refresh_with_user_token_fails(client: AsyncClient, user_token: str):
    """User token cannot be used for admin refresh."""
    resp = await client.post("/api/v1/auth/admin/refresh", json={"refresh_token": user_token})
    assert resp.status_code == 401


async def test_suspended_admin_cannot_login(client: AsyncClient, test_admin, db):
    from app.models.admin_user import AdminUser
    from sqlalchemy import select

    admin_id, email, password = test_admin
    result = await db.execute(select(AdminUser).where(AdminUser.id == uuid.UUID(admin_id)))
    admin = result.scalar_one()
    admin.status = "suspended"
    await db.commit()

    resp = await client.post("/api/v1/auth/admin/login", json={"email": email, "password": password})
    assert resp.status_code == 403
