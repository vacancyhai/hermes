"""Authentication endpoints.

POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/logout
POST /api/v1/auth/refresh
POST /api/v1/auth/forgot-password
POST /api/v1/auth/reset-password
GET  /api/v1/auth/verify-email/:token
GET  /api/v1/auth/csrf-token
"""

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_current_user, get_db, get_redis
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenResponse,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def _create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    to_encode["jti"] = str(uuid.uuid4())
    to_encode["exp"] = datetime.now(timezone.utc) + expires_delta
    to_encode["iat"] = datetime.now(timezone.utc)
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(user_id: str, role: str) -> str:
    return _create_token(
        {"sub": user_id, "role": role, "type": "access"},
        timedelta(seconds=settings.JWT_ACCESS_TOKEN_EXPIRES),
    )


def create_refresh_token(user_id: str, role: str) -> str:
    return _create_token(
        {"sub": user_id, "role": role, "type": "refresh"},
        timedelta(seconds=settings.JWT_REFRESH_TOKEN_EXPIRES),
    )


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Create a new user account."""
    result = await db.execute(select(User).where(User.email == body.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=body.email,
        password_hash=pwd_context.hash(body.password),
        full_name=body.full_name,
    )
    db.add(user)
    await db.flush()

    profile = UserProfile(user_id=user.id)
    db.add(profile)

    return RegisterResponse(id=user.id, email=user.email, full_name=user.full_name, role=user.role)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate and return JWT token pair."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not pwd_context.verify(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if user.status == "suspended":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account suspended")

    if user.status == "deleted":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    user.last_login = datetime.now(timezone.utc)

    return TokenResponse(
        access_token=create_access_token(str(user.id), user.role),
        refresh_token=create_refresh_token(str(user.id), user.role),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user=Depends(get_current_user), redis=Depends(get_redis)):
    """Invalidate current JWT by adding JTI to Redis blocklist."""
    user, payload = current_user
    jti = payload.get("jti")
    if jti:
        exp = payload.get("exp", 0)
        ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 1)
        await redis.setex(f"blocklist:{jti}", ttl, "1")


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db), redis=Depends(get_redis)):
    """Refresh JWT token pair. Rotates both tokens and blocklists the old refresh."""
    try:
        payload = jwt.decode(body.refresh_token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    jti = payload.get("jti")
    if jti and await redis.get(f"blocklist:{jti}"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    # Blocklist old refresh token
    exp = payload.get("exp", 0)
    ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 1)
    await redis.setex(f"blocklist:{jti}", ttl, "1")

    return TokenResponse(
        access_token=create_access_token(str(user.id), user.role),
        refresh_token=create_refresh_token(str(user.id), user.role),
    )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db), redis=Depends(get_redis)):
    """Send password reset email. Always returns 200 to prevent email enumeration."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user:
        reset_token = secrets.token_urlsafe(32)
        await redis.setex(f"reset:{reset_token}", 3600, str(user.id))
        # TODO: Queue Celery email task with reset_token

    return MessageResponse(message="If the email exists, a reset link has been sent.")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db), redis=Depends(get_redis)):
    """Reset password using token."""
    user_id_str = await redis.get(f"reset:{body.token}")
    if not user_id_str:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    user_id_str = user_id_str.decode() if isinstance(user_id_str, bytes) else user_id_str
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id_str)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    user.password_hash = pwd_context.hash(body.new_password)
    await redis.delete(f"reset:{body.token}")

    return MessageResponse(message="Password reset successful.")


@router.get("/verify-email/{token}", response_model=MessageResponse)
async def verify_email(token: str, db: AsyncSession = Depends(get_db), redis=Depends(get_redis)):
    """Verify email address using token."""
    user_id_str = await redis.get(f"verify:{token}")
    if not user_id_str:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token")

    user_id_str = user_id_str.decode() if isinstance(user_id_str, bytes) else user_id_str
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id_str)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired verification token")

    user.is_email_verified = True
    await redis.delete(f"verify:{token}")

    return MessageResponse(message="Email verified successfully.")


@router.get("/csrf-token")
async def csrf_token(redis=Depends(get_redis)):
    """Generate a CSRF token."""
    token = secrets.token_urlsafe(32)
    await redis.setex(f"csrf:{token}", 3600, "1")
    return {"csrf_token": token}
