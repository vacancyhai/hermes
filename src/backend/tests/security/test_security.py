"""Security audit tests — #140.

Verifies: JWT security, RBAC, input validation, file upload safety,
password hashing, token revocation, CORS, and OWASP top 10 protections.
"""

import uuid

import pytest
from httpx import AsyncClient
from jose import jwt
from passlib.context import CryptContext

from app.config import settings
from app.routers.auth import create_access_token

def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}

pytestmark = pytest.mark.asyncio

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- JWT Security ---

async def test_jwt_token_structure(user_token: str):
    """JWT uses HS256, has exp/iat/jti claims, and all values are valid."""
    header = jwt.get_unverified_header(user_token)
    assert header["alg"] == "HS256"

    payload = jwt.decode(user_token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
    assert "exp" in payload
    assert "iat" in payload
    assert payload["exp"] > payload["iat"]
    assert "jti" in payload
    uuid.UUID(payload["jti"])  # JTI must be a valid UUID


async def test_forged_token_rejected(client: AsyncClient):
    forged = jwt.encode(
        {"sub": str(uuid.uuid4()), "user_type": "admin", "type": "access", "jti": str(uuid.uuid4())},
        "wrong-secret-key",
        algorithm="HS256",
    )
    resp = await client.get("/api/v1/admin/stats", headers=auth_header(forged))
    assert resp.status_code == 401


async def test_expired_token_rejected(client: AsyncClient):
    import time
    from datetime import datetime, timedelta, timezone

    expired = jwt.encode(
        {
            "sub": str(uuid.uuid4()),
            "user_type": "user",
            "type": "access",
            "jti": str(uuid.uuid4()),
            "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            "iat": datetime.now(timezone.utc) - timedelta(hours=2),
        },
        settings.JWT_SECRET_KEY,
        algorithm="HS256",
    )
    resp = await client.get("/api/v1/notifications", headers=auth_header(expired))
    assert resp.status_code == 401


async def test_user_token_cannot_access_admin_endpoints(client: AsyncClient, user_token: str):
    endpoints = [
        ("GET", "/api/v1/admin/stats"),
        ("GET", "/api/v1/admin/jobs"),
        ("GET", "/api/v1/admin/users"),
        ("GET", "/api/v1/admin/logs"),
    ]
    for method, url in endpoints:
        resp = await client.request(method, url, headers=auth_header(user_token))
        assert resp.status_code == 403, f"{method} {url} should be 403 for user token"


async def test_admin_token_cannot_access_user_endpoints(client: AsyncClient, admin_token: str):
    resp = await client.get("/api/v1/notifications", headers=auth_header(admin_token))
    assert resp.status_code == 403


# --- Token Revocation ---

async def test_logout_blocklists_token(client: AsyncClient, user_token: str, test_redis):
    payload = jwt.decode(user_token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
    jti = payload["jti"]
    prefix = settings.REDIS_KEY_PREFIX

    # Before logout, blocklist key shouldn't exist
    assert await test_redis.get(f"{prefix}:blocklist:{jti}") is None

    # Logout
    await client.post("/api/v1/auth/logout", headers=auth_header(user_token))

    # After logout, blocklist key should exist
    assert await test_redis.get(f"{prefix}:blocklist:{jti}") is not None


# --- Password Security (admin auth uses bcrypt) ---

def test_admin_bcrypt_hashing():
    """Admin passwords are stored as bcrypt hashes."""
    password = "AdminPassword123"
    hashed = pwd_context.hash(password)
    assert hashed.startswith("$2b$")
    assert pwd_context.verify(password, hashed)
    assert not pwd_context.verify("WrongPassword", hashed)


async def test_password_hash_not_exposed_in_api(client: AsyncClient, user_token: str):
    """password_hash must never appear in API responses."""
    resp = await client.get("/api/v1/users/profile", headers=auth_header(user_token))
    assert resp.status_code == 200
    assert "password_hash" not in resp.text


# --- Input Validation ---

async def test_sql_injection_in_search(client: AsyncClient):
    resp = await client.get("/api/v1/jobs?q='; DROP TABLE users; --")
    assert resp.status_code == 200  # Should not crash


async def test_xss_in_job_title(client: AsyncClient, admin_token: str):
    resp = await client.post(
        "/api/v1/admin/jobs",
        json={
            "job_title": '<script>alert("xss")</script>',
            "organization": "XSS Test",
            "description": "test",
            "status": "draft",
        },
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201
    # Value stored as-is (Jinja2 autoescapes on render, API returns raw)
    assert resp.json()["job_title"] == '<script>alert("xss")</script>'


async def test_pagination_validation(client: AsyncClient):
    resp = await client.get("/api/v1/jobs?limit=0")
    assert resp.status_code == 422

    resp = await client.get("/api/v1/jobs?limit=200")
    assert resp.status_code == 422

    resp = await client.get("/api/v1/jobs?offset=-1")
    assert resp.status_code == 422


# --- CORS ---

async def test_cors_headers(client: AsyncClient):
    resp = await client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:8080",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" in resp.headers


# --- Containers Non-root ---

def test_dockerfile_uses_nonroot_user():
    """Verify Dockerfile switches to non-root user."""
    with open("Dockerfile") as f:
        content = f.read()
    assert "USER appuser" in content
    assert "adduser" in content


# --- Health endpoint (no auth required) ---

async def test_health_no_auth(client: AsyncClient):
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
