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


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Validate JWT and return (user, token_payload) tuple."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    # Check blocklist
    jti = payload.get("jti")
    if jti and await redis.get(f"blocklist:{jti}"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    from app.models.user import User

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return user, payload


async def require_admin(current_user=Depends(get_current_user)):
    """Require the current user to have admin role."""
    user, _ = current_user
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user


async def require_operator(current_user=Depends(get_current_user)):
    """Require the current user to have operator or admin role."""
    user, _ = current_user
    if user.role not in ("operator", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operator access required")
    return user
