"""Authentication endpoints.

User endpoints (Firebase Auth):
  POST /api/v1/auth/verify-token
  POST /api/v1/auth/logout
  POST /api/v1/auth/refresh

Admin endpoints (local bcrypt + JWT):
  POST /api/v1/auth/admin/login
  POST /api/v1/auth/admin/logout
  POST /api/v1/auth/admin/refresh
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.config import settings
from app.dependencies import get_current_admin, get_current_user, get_db, get_redis
from app.models.admin_log import AdminLog
from app.models.admin_user import AdminUser
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.auth import (
    AdminLoginRequest,
    FirebaseVerifyRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    TokenResponse,
)

from app.rate_limit import limiter

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# Used only for admin auth (users authenticate via Firebase)
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


# ─── User Auth (Firebase) ────────────────────────────────────────────────────


@router.post("/verify-token", response_model=TokenResponse)
@limiter.limit("10/minute")
async def verify_token(request: Request, body: FirebaseVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Verify Firebase ID token, upsert user, return internal JWT pair.

    Lookup order: firebase_uid → email → create new user.
    Replaces /register, /login, and /google-verify.
    """
    from app.firebase import verify_id_token

    try:
        decoded = verify_id_token(body.id_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Firebase token")

    firebase_uid = decoded["uid"]
    email = (decoded.get("email") or "").lower() or None
    phone = decoded.get("phone_number")  # E.164 format from Firebase phone auth
    name = decoded.get("name") or body.full_name or email or phone or "User"
    email_verified = decoded.get("email_verified", False)
    provider = decoded.get("firebase", {}).get("sign_in_provider", "unknown")

    # 1. Find by firebase_uid
    result = await db.execute(select(User).where(User.firebase_uid == firebase_uid))
    user = result.scalar_one_or_none()

    if not user and email:
        # 2. Find by email (legacy user re-authenticating via Firebase)
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            user.firebase_uid = firebase_uid
            user.migration_status = "migrated"

    if user:
        if user.status == "suspended":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account suspended")
        if user.status == "deleted":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account not found")
        user.last_login = datetime.now(timezone.utc)
        if email_verified and not user.is_email_verified:
            user.is_email_verified = True
        if phone and not user.phone:
            user.phone = phone
        if email and not user.email:
            user.email = email
    else:
        # 3. New user — create account
        user = User(
            email=email,
            firebase_uid=firebase_uid,
            full_name=name,
            is_email_verified=email_verified,
            phone=phone,
            migration_status="native",
        )
        db.add(user)
        await db.flush()
        db.add(UserProfile(user_id=user.id))

    ip = request.client.host if request.client else "unknown"
    logger.info("firebase_auth", extra={"user_id": str(user.id), "provider": provider, "ip": ip})

    return TokenResponse(
        access_token=create_access_token(str(user.id), "user"),
        refresh_token=create_refresh_token(str(user.id), "user"),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: LogoutRequest = LogoutRequest(),
    current_user=Depends(get_current_user),
    redis=Depends(get_redis),
):
    """Invalidate current user JWT by adding JTI to Redis blocklist.

    Accepts an optional refresh_token in the body. If provided, its JTI is
    also blocklisted so the token cannot be used to obtain new access tokens.
    """
    user, payload = current_user
    jti = payload.get("jti")
    if jti:
        exp = payload.get("exp", 0)
        ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 1)
        await redis.setex(f"{settings.REDIS_KEY_PREFIX}:blocklist:{jti}", ttl, "1")

    if body.refresh_token:
        try:
            rt_payload = jwt.decode(body.refresh_token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
            rt_jti = rt_payload.get("jti")
            if rt_jti and rt_payload.get("type") == "refresh" and rt_payload.get("user_type") == "user":
                rt_exp = rt_payload.get("exp", 0)
                rt_ttl = max(int(rt_exp - datetime.now(timezone.utc).timestamp()), 1)
                await redis.setex(f"{settings.REDIS_KEY_PREFIX}:blocklist:{rt_jti}", rt_ttl, "1")
        except JWTError:
            pass  # Malformed refresh token — ignore; access token already blocklisted

    logger.info("logout", extra={"user_id": str(user.id)})


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
    if jti and await redis.get(f"{settings.REDIS_KEY_PREFIX}:blocklist:{jti}"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or user.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    exp = payload.get("exp", 0)
    ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 1)
    await redis.setex(f"{settings.REDIS_KEY_PREFIX}:blocklist:{jti}", ttl, "1")

    logger.info("token_refreshed", extra={"user_id": str(user.id)})
    return TokenResponse(
        access_token=create_access_token(str(user.id), "user"),
        refresh_token=create_refresh_token(str(user.id), "user"),
    )


# ─── Admin Auth (local bcrypt + JWT — unchanged) ─────────────────────────────


@router.post("/admin/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def admin_login(request: Request, body: AdminLoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate admin/operator and return JWT token pair."""
    result = await db.execute(select(AdminUser).where(AdminUser.email == body.email))
    admin = result.scalar_one_or_none()

    ip = request.client.host if request.client else "unknown"
    if not admin or not pwd_context.verify(body.password, admin.password_hash):
        logger.warning("admin_login_failed", extra={"email": body.email, "ip": ip})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if admin.status == "suspended":
        logger.warning("admin_login_suspended", extra={"email": body.email, "ip": ip})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account suspended")

    if admin.status == "deleted":
        logger.warning("admin_login_failed", extra={"email": body.email, "ip": ip})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    admin.last_login = datetime.now(timezone.utc)
    logger.info("admin_login_success", extra={"admin_id": str(admin.id), "role": admin.role, "ip": ip})

    db.add(AdminLog(
        admin_id=admin.id,
        action="admin_login",
        details=f"Login from {ip}",
        ip_address=ip,
        user_agent=request.headers.get("user-agent"),
    ))

    return TokenResponse(
        access_token=create_access_token(str(admin.id), "admin", admin.role),
        refresh_token=create_refresh_token(str(admin.id), "admin", admin.role),
    )


@router.post("/admin/logout", status_code=status.HTTP_204_NO_CONTENT)
async def admin_logout(
    request: Request,
    body: LogoutRequest = LogoutRequest(),
    current_admin=Depends(get_current_admin),
    redis=Depends(get_redis),
    db: AsyncSession = Depends(get_db),
):
    """Invalidate current admin JWT by adding JTI to Redis blocklist.

    Accepts an optional refresh_token in the body. If provided, its JTI is
    also blocklisted so the token cannot be used to obtain new access tokens.
    """
    admin, payload = current_admin
    jti = payload.get("jti")
    if jti:
        exp = payload.get("exp", 0)
        ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 1)
        await redis.setex(f"{settings.REDIS_KEY_PREFIX}:blocklist:{jti}", ttl, "1")

    if body.refresh_token:
        try:
            rt_payload = jwt.decode(body.refresh_token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
            rt_jti = rt_payload.get("jti")
            if rt_jti and rt_payload.get("type") == "refresh" and rt_payload.get("user_type") == "admin":
                rt_exp = rt_payload.get("exp", 0)
                rt_ttl = max(int(rt_exp - datetime.now(timezone.utc).timestamp()), 1)
                await redis.setex(f"{settings.REDIS_KEY_PREFIX}:blocklist:{rt_jti}", rt_ttl, "1")
        except JWTError:
            pass

    logger.info("admin_logout", extra={"admin_id": str(admin.id)})

    ip = request.client.host if request.client else "unknown"
    db.add(AdminLog(
        admin_id=admin.id,
        action="admin_logout",
        details=f"Logout from {ip}",
        ip_address=ip,
        user_agent=request.headers.get("user-agent"),
    ))


@router.post("/admin/refresh", response_model=TokenResponse)
async def admin_refresh(
    request: Request,
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """Refresh admin JWT token pair."""
    try:
        payload = jwt.decode(body.refresh_token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if payload.get("type") != "refresh" or payload.get("user_type") != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    jti = payload.get("jti")
    if jti and await redis.get(f"{settings.REDIS_KEY_PREFIX}:blocklist:{jti}"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    admin_id = payload.get("sub")
    result = await db.execute(select(AdminUser).where(AdminUser.id == uuid.UUID(admin_id)))
    admin = result.scalar_one_or_none()
    if not admin or admin.status != "active":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin not found or inactive")

    exp = payload.get("exp", 0)
    ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 1)
    await redis.setex(f"{settings.REDIS_KEY_PREFIX}:blocklist:{jti}", ttl, "1")

    ip = request.client.host if request.client else "unknown"
    db.add(AdminLog(
        admin_id=admin.id,
        action="admin_token_refresh",
        details=f"Token refreshed from {ip}",
        ip_address=ip,
        user_agent=request.headers.get("user-agent"),
    ))

    return TokenResponse(
        access_token=create_access_token(str(admin.id), "admin", admin.role),
        refresh_token=create_refresh_token(str(admin.id), "admin", admin.role),
    )
