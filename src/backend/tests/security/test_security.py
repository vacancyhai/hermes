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

def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}

pytestmark = pytest.mark.asyncio

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- JWT Security ---

async def test_jwt_uses_hs256_only(client: AsyncClient, test_user):
    _, email, password = test_user
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    header = jwt.get_unverified_header(token)
    assert header["alg"] == "HS256"


async def test_jwt_has_expiry(client: AsyncClient, test_user):
    _, email, password = test_user
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    payload = jwt.decode(resp.json()["access_token"], settings.JWT_SECRET_KEY, algorithms=["HS256"])
    assert "exp" in payload
    assert "iat" in payload
    assert payload["exp"] > payload["iat"]


async def test_jwt_has_jti_for_revocation(client: AsyncClient, test_user):
    _, email, password = test_user
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    payload = jwt.decode(resp.json()["access_token"], settings.JWT_SECRET_KEY, algorithms=["HS256"])
    assert "jti" in payload
    # JTI should be a valid UUID
    uuid.UUID(payload["jti"])


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
    resp = await client.get("/api/v1/applications/stats", headers=auth_header(expired))
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
    resp = await client.get("/api/v1/applications/stats", headers=auth_header(admin_token))
    assert resp.status_code == 403


# --- Token Revocation ---

async def test_logout_blocklists_token(client: AsyncClient, test_user, test_redis):
    _, email, password = test_user
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
    jti = payload["jti"]

    # Before logout, blocklist key shouldn't exist
    assert await test_redis.get(f"blocklist:{jti}") is None

    # Logout
    await client.post("/api/v1/auth/logout", headers=auth_header(token))

    # After logout, blocklist key should exist
    assert await test_redis.get(f"blocklist:{jti}") is not None


# --- Password Security ---

async def test_bcrypt_hashing():
    password = "TestPassword123"
    hashed = pwd_context.hash(password)
    assert hashed.startswith("$2b$")
    assert pwd_context.verify(password, hashed)
    assert not pwd_context.verify("WrongPassword", hashed)


async def test_password_not_in_response(client: AsyncClient):
    email = f"nopw_{uuid.uuid4().hex[:8]}@test.com"
    resp = await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "SecurePass123",
        "full_name": "No PW User",
    })
    body = resp.text
    assert "SecurePass123" not in body
    assert "password_hash" not in body


# --- File Upload Security ---

async def test_upload_rejects_non_pdf(client: AsyncClient, admin_token: str):
    resp = await client.post(
        "/api/v1/admin/jobs/upload-pdf",
        files={"file": ("test.txt", b"not a pdf", "text/plain")},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 400
    assert "pdf" in resp.json()["error"]["message"].lower()


async def test_upload_rejects_oversized_file(client: AsyncClient, admin_token: str):
    # Create a file just over 10MB
    big_content = b"%PDF-1.4\n" + b"x" * (11 * 1024 * 1024)
    resp = await client.post(
        "/api/v1/admin/jobs/upload-pdf",
        files={"file": ("big.pdf", big_content, "application/pdf")},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 400
    assert "exceed" in resp.json()["error"]["message"].lower() or "limit" in resp.json()["error"]["message"].lower()


async def test_upload_requires_auth(client: AsyncClient):
    resp = await client.post(
        "/api/v1/admin/jobs/upload-pdf",
        files={"file": ("test.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert resp.status_code in (401, 403)


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
            "job_type": "latest_job",
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
