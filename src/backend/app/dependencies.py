"""FastAPI dependencies — database session, auth, Redis."""

import uuid
from typing import AsyncGenerator

import redis.asyncio as aioredis
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session

security = HTTPBearer()

ALGORITHM = "HS256"

# Redis connection pool (lazy singleton)
_redis_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Return an async Redis client."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(settings.REDIS_URL, decode_responses=False)
    return _redis_pool


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session. Used as a FastAPI dependency."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def _decode_and_validate_token(
    credentials: HTTPAuthorizationCredentials,
    redis: aioredis.Redis,
    expected_user_type: str,
):
    """Decode JWT, check blocklist, and validate user_type. Returns payload dict."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    if payload.get("user_type") != expected_user_type:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token scope")

    jti = payload.get("jti")
    if jti and await redis.get(f"blocklist:{jti}"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    if not payload.get("sub"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    return payload


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Validate JWT and return (user, token_payload) tuple for regular users."""
    payload = await _decode_and_validate_token(credentials, redis, "user")

    from app.models.user import User

    result = await db.execute(select(User).where(User.id == uuid.UUID(payload["sub"])))
    user = result.scalar_one_or_none()
    if not user or user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user, payload


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Validate JWT and return (admin, token_payload) tuple for admin/operator."""
    payload = await _decode_and_validate_token(credentials, redis, "admin")

    from app.models.admin_user import AdminUser

    result = await db.execute(select(AdminUser).where(AdminUser.id == uuid.UUID(payload["sub"])))
    admin = result.scalar_one_or_none()
    if not admin or admin.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin not found or inactive")

    return admin, payload


async def require_admin(current_admin=Depends(get_current_admin)):
    """Require the current admin to have admin role (not operator)."""
    admin, _ = current_admin
    if admin.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return admin


async def require_operator(current_admin=Depends(get_current_admin)):
    """Require the current admin to have operator or admin role."""
    admin, _ = current_admin
    if admin.role not in ("operator", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operator access required")
    return admin
