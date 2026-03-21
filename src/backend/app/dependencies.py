"""FastAPI dependencies — database session, auth, etc."""

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session

security = HTTPBearer()


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
):
    """Validate JWT and return the current user.

    TODO: Implement JWT decode, Redis blocklist check, user lookup.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Auth not yet implemented",
    )


async def require_admin(current_user=Depends(get_current_user)):
    """Require the current user to have admin role.

    TODO: Check current_user.role == 'admin'.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Admin check not yet implemented",
    )


async def require_operator(current_user=Depends(get_current_user)):
    """Require the current user to have operator or admin role.

    TODO: Check current_user.role in ('operator', 'admin').
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Operator check not yet implemented",
    )
