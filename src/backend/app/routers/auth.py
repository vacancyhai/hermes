"""Authentication endpoints.

User endpoints:
  POST /api/v1/auth/register
  POST /api/v1/auth/login
  POST /api/v1/auth/logout
  POST /api/v1/auth/refresh
  POST /api/v1/auth/forgot-password
  POST /api/v1/auth/reset-password
  GET  /api/v1/auth/verify-email/:token
  GET  /api/v1/auth/csrf-token

Admin endpoints:
  POST /api/v1/auth/admin/login
  POST /api/v1/auth/admin/logout
  POST /api/v1/auth/admin/refresh
"""

import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.dependencies import get_current_admin, get_current_user, get_db, get_redis
from app.models.admin_user import AdminUser
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.auth import (
    AdminLoginRequest,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenResponse,
)

from app.rate_limit import limiter

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def _create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    to_encode["jti"] = str(uuid.uuid4())
    to_encode["exp"] = datetime.now(timezone.utc) + expires_delta
    to_encode["iat"] = datetime.now(timezone.utc)
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(user_id: str, user_type: str, role: str | None = None) -> str:
    data = {"sub": user_id, "user_type": user_type, "type": "access"}
    if role:
        data["role"] = role
    return _create_token(data, timedelta(seconds=settings.JWT_ACCESS_TOKEN_EXPIRES))


def create_refresh_token(user_id: str, user_type: str, role: str | None = None) -> str:
    data = {"sub": user_id, "user_type": user_type, "type": "refresh"}
    if role:
        data["role"] = role
    return _create_token(data, timedelta(seconds=settings.JWT_REFRESH_TOKEN_EXPIRES))


# ─── User Auth ───────────────────────────────────────────────────────────────


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, body: RegisterRequest, db: AsyncSession = Depends(get_db)):
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

    return RegisterResponse(id=user.id, email=user.email, full_name=user.full_name)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate regular user and return JWT token pair."""
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
        access_token=create_access_token(str(user.id), "user"),
        refresh_token=create_refresh_token(str(user.id), "user"),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user=Depends(get_current_user), redis=Depends(get_redis)):
    """Invalidate current user JWT by adding JTI to Redis blocklist."""
    user, payload = current_user
    jti = payload.get("jti")
    if jti:
        exp = payload.get("exp", 0)
        ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 1)
        await redis.setex(f"blocklist:{jti}", ttl, "1")


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db), redis=Depends(get_redis)):
    """Refresh user JWT token pair."""
    try:
        payload = jwt.decode(body.refresh_token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if payload.get("type") != "refresh" or payload.get("user_type") != "user":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    jti = payload.get("jti")
    if jti and await redis.get(f"blocklist:{jti}"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    exp = payload.get("exp", 0)
    ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 1)
    await redis.setex(f"blocklist:{jti}", ttl, "1")

    return TokenResponse(
        access_token=create_access_token(str(user.id), "user"),
        refresh_token=create_refresh_token(str(user.id), "user"),
    )


@router.post("/forgot-password", response_model=MessageResponse)
@limiter.limit("3/minute")
async def forgot_password(request: Request, body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db), redis=Depends(get_redis)):
    """Send password reset email. Always returns 200 to prevent email enumeration."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user:
        reset_token = secrets.token_urlsafe(32)
        await redis.setex(f"reset:user:{reset_token}", 3600, str(user.id))
        from app.tasks.notifications import send_email_notification
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        send_email_notification.delay(
            user.email,
            "Reset your Hermes password",
            "password_reset.html",
            {"name": user.full_name or user.email, "reset_url": reset_url},
        )

    return MessageResponse(message="If the email exists, a reset link has been sent.")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db), redis=Depends(get_redis)):
    """Reset user password using token."""
    user_id_str = await redis.get(f"reset:user:{body.token}")
    if not user_id_str:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    user_id_str = user_id_str.decode() if isinstance(user_id_str, bytes) else user_id_str
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id_str)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token")

    user.password_hash = pwd_context.hash(body.new_password)
    await redis.delete(f"reset:user:{body.token}")

    return MessageResponse(message="Password reset successful.")


@router.get("/verify-email/{token}", response_model=MessageResponse)
async def verify_email(token: str, db: AsyncSession = Depends(get_db), redis=Depends(get_redis)):
    """Verify user email address using token."""
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


# ─── Admin Auth ──────────────────────────────────────────────────────────────


@router.post("/admin/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def admin_login(request: Request, body: AdminLoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate admin/operator and return JWT token pair."""
    result = await db.execute(select(AdminUser).where(AdminUser.email == body.email))
    admin = result.scalar_one_or_none()

    if not admin or not pwd_context.verify(body.password, admin.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if admin.status == "suspended":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account suspended")

    if admin.status == "deleted":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    admin.last_login = datetime.now(timezone.utc)

    return TokenResponse(
        access_token=create_access_token(str(admin.id), "admin", admin.role),
        refresh_token=create_refresh_token(str(admin.id), "admin", admin.role),
    )


@router.post("/admin/logout", status_code=status.HTTP_204_NO_CONTENT)
async def admin_logout(current_admin=Depends(get_current_admin), redis=Depends(get_redis)):
    """Invalidate current admin JWT by adding JTI to Redis blocklist."""
    admin, payload = current_admin
    jti = payload.get("jti")
    if jti:
        exp = payload.get("exp", 0)
        ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 1)
        await redis.setex(f"blocklist:{jti}", ttl, "1")


@router.post("/admin/refresh", response_model=TokenResponse)
async def admin_refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db), redis=Depends(get_redis)):
    """Refresh admin JWT token pair."""
    try:
        payload = jwt.decode(body.refresh_token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if payload.get("type") != "refresh" or payload.get("user_type") != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    jti = payload.get("jti")
    if jti and await redis.get(f"blocklist:{jti}"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    admin_id = payload.get("sub")
    result = await db.execute(select(AdminUser).where(AdminUser.id == uuid.UUID(admin_id)))
    admin = result.scalar_one_or_none()
    if not admin or admin.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin not found or inactive")

    exp = payload.get("exp", 0)
    ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 1)
    await redis.setex(f"blocklist:{jti}", ttl, "1")

    return TokenResponse(
        access_token=create_access_token(str(admin.id), "admin", admin.role),
        refresh_token=create_refresh_token(str(admin.id), "admin", admin.role),
    )
