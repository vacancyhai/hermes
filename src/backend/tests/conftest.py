"""Test configuration — async fixtures for DB, client, auth tokens.

All tests run against the real FastAPI app with SEPARATE test database and Redis.
Set TEST_DATABASE_URL to use a different database (recommended: hermes_test_db).
A fresh async engine is created per test to avoid event-loop mismatch.
"""

import os
import uuid

import pytest
import pytest_asyncio
import redis.asyncio as aioredis
from app.config import settings
from app.dependencies import get_db, get_redis
from app.main import app
from app.rate_limit import limiter
from httpx import ASGITransport, AsyncClient
from passlib.context import CryptContext
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Disable rate limiting for the entire test suite so auth fixtures don't hit 429
limiter.enabled = False

_TRUNCATE_TABLES = [
    "notification_delivery_log",
    "notifications",
    "user_watches",
    "user_devices",
    "admin_logs",
    "admit_cards",
    "answer_keys",
    "results",
    "jobs",
    "admissions",
    "user_profiles",
    "users",
    "admin_users",
]


def _get_test_database_url():
    """Get test database URL from environment or fall back to settings."""
    return os.getenv("TEST_DATABASE_URL", settings.DATABASE_URL)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def truncate_all_tables():
    """Truncate all tables before the test session to ensure a clean slate.

    Uses TEST_DATABASE_URL if set, otherwise uses main DATABASE_URL.
    Without this, data committed by previous test runs accumulates in the DB
    (the per-test db fixture rolls back only, but the client fixture commits).
    """
    test_db_url = _get_test_database_url()
    engine = create_async_engine(
        test_db_url,
        connect_args={"prepared_statement_cache_size": 0},
    )
    async with engine.connect() as conn:
        tables = ", ".join(_TRUNCATE_TABLES)
        await conn.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))
        await conn.commit()
    await engine.dispose()
    yield


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Import token helpers for test fixtures (avoids calling removed /auth/login endpoint)
from app.routers.auth import create_access_token, create_refresh_token


@pytest_asyncio.fixture
async def test_engine():
    test_db_url = _get_test_database_url()
    eng = create_async_engine(
        test_db_url,
        pool_size=5,
        pool_pre_ping=True,
        connect_args={"prepared_statement_cache_size": 0},
    )
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture
async def test_redis():
    r = aioredis.from_url(settings.REDIS_URL, decode_responses=False)
    yield r
    await r.aclose()


@pytest_asyncio.fixture
async def db(test_engine):
    session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(test_engine, test_redis):
    session_factory = async_sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def override_redis():
        return test_redis

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis] = override_redis
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db: AsyncSession):
    """Create a fresh test user and return (user_id, email, password).

    Users now authenticate via Firebase — password_hash is nullable but set here
    for legacy compatibility. firebase_uid is set for tests that call verify-token.
    """
    from app.models.user import User
    from app.models.user_profile import UserProfile

    email = f"testuser_{uuid.uuid4().hex[:8]}@test.com"
    password = "TestPass123"
    user = User(
        email=email,
        password_hash=pwd_context.hash(
            password
        ),  # kept nullable; used by some legacy tests
        firebase_uid=f"test-firebase-uid-{uuid.uuid4().hex[:12]}",
        full_name="Test User",
        status="active",
        migration_status="native",
    )
    db.add(user)
    await db.flush()

    profile = UserProfile(user_id=user.id)
    db.add(profile)
    await db.commit()

    return str(user.id), email, password


@pytest_asyncio.fixture
async def test_admin(db: AsyncSession):
    """Create a fresh admin user and return (admin_id, email, password)."""
    from app.models.admin_user import AdminUser

    email = f"testadmin_{uuid.uuid4().hex[:8]}@test.com"
    password = "AdminPass123"
    admin = AdminUser(
        email=email,
        password_hash=pwd_context.hash(password),
        full_name="Test Admin",
        role="admin",
        department="Test Department",
        status="active",
    )
    db.add(admin)
    await db.commit()

    return str(admin.id), email, password


@pytest_asyncio.fixture
async def test_operator(db: AsyncSession):
    """Create a fresh operator user and return (operator_id, email, password)."""
    from app.models.admin_user import AdminUser

    email = f"testoperator_{uuid.uuid4().hex[:8]}@test.com"
    password = "OperPass123"
    operator = AdminUser(
        email=email,
        password_hash=pwd_context.hash(password),
        full_name="Test Operator",
        role="operator",
        department="Test Department",
        status="active",
    )
    db.add(operator)
    await db.commit()

    return str(operator.id), email, password


@pytest_asyncio.fixture
async def user_token(test_user):
    """Get a valid user JWT access token (created directly — /auth/login removed)."""
    user_id, _, _ = test_user
    return create_access_token(user_id, "user")


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, test_admin):
    """Get a valid admin JWT access token."""
    _, email, password = test_admin
    resp = await client.post(
        "/api/v1/auth/admin/login", json={"email": email, "password": password}
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def operator_token(client: AsyncClient, test_operator):
    """Get a valid operator JWT access token."""
    _, email, password = test_operator
    resp = await client.post(
        "/api/v1/auth/admin/login", json={"email": email, "password": password}
    )
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def active_job(client: AsyncClient, admin_token: str):
    """Create an active job and return the full response dict."""
    resp = await client.post(
        "/api/v1/admin/jobs",
        json={
            "job_title": f"Test Job {uuid.uuid4().hex[:6]}",
            "organization": "Test Organization",
            "qualification_level": "graduate",
            "total_vacancies": 100,
            "description": "A test job vacancy for automated testing.",
            "status": "active",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    return resp.json()


@pytest_asyncio.fixture
async def draft_job(client: AsyncClient, admin_token: str):
    """Create a draft job and return the full response dict."""
    resp = await client.post(
        "/api/v1/admin/jobs",
        json={
            "job_title": f"Draft Job {uuid.uuid4().hex[:6]}",
            "organization": "Draft Organization",
            "description": "A draft test job.",
            "status": "draft",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    return resp.json()


@pytest_asyncio.fixture
async def active_admission(client: AsyncClient, admin_token: str):
    """Create an active admission and return the full response dict."""
    resp = await client.post(
        "/api/v1/admin/admissions",
        json={
            "exam_name": f"Test Exam {uuid.uuid4().hex[:6]}",
            "conducting_body": "NTA",
            "stream": "engineering",
            "status": "active",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    return resp.json()


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
