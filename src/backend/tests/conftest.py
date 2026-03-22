"""Test configuration — async fixtures for DB, client, auth tokens.

All tests run against the real FastAPI app with real database and Redis.
A fresh async engine is created per test to avoid event-loop mismatch.
"""

import uuid

import pytest
import pytest_asyncio
import redis.asyncio as aioredis
from httpx import ASGITransport, AsyncClient
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.dependencies import get_db, get_redis
from app.main import app

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@pytest_asyncio.fixture
async def test_engine():
    eng = create_async_engine(
        settings.DATABASE_URL,
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
    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(test_engine, test_redis):
    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

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
    """Create a fresh test user and return (user_id, email, password)."""
    from app.models.user import User
    from app.models.user_profile import UserProfile

    email = f"testuser_{uuid.uuid4().hex[:8]}@test.com"
    password = "TestPass123"
    user = User(
        email=email,
        password_hash=pwd_context.hash(password),
        full_name="Test User",
        status="active",
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
async def user_token(client: AsyncClient, test_user):
    """Get a valid user JWT access token."""
    _, email, password = test_user
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, test_admin):
    """Get a valid admin JWT access token."""
    _, email, password = test_admin
    resp = await client.post("/api/v1/auth/admin/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def operator_token(client: AsyncClient, test_operator):
    """Get a valid operator JWT access token."""
    _, email, password = test_operator
    resp = await client.post("/api/v1/auth/admin/login", json={"email": email, "password": password})
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
            "job_type": "latest_job",
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
            "job_type": "latest_job",
            "description": "A draft test job.",
            "status": "draft",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 201
    return resp.json()


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
