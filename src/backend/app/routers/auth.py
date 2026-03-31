"""Authentication endpoints.

User endpoints (Firebase Auth):
  POST /api/v1/auth/verify-token
  POST /api/v1/auth/logout
  POST /api/v1/auth/refresh

Email OTP (registration verification):
  POST /api/v1/auth/send-email-otp
  POST /api/v1/auth/verify-email-otp
  POST /api/v1/auth/complete-registration

Admin endpoints (local bcrypt + JWT):
  POST /api/v1/auth/admin/login
  POST /api/v1/auth/admin/logout
  POST /api/v1/auth/admin/refresh
"""

import asyncio
import logging
import os
import secrets
import smtplib
import uuid
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Environment, FileSystemLoader

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
    AdminUserResponse,
    CompleteRegistrationRequest,
    EmailOTPRequest,
    EmailOTPVerifyRequest,
    FirebaseCustomTokenResponse,
    FirebaseVerifyRequest,
    LogoutRequest,
    MessageResponse,
    OTPVerifiedResponse,
    RefreshRequest,
    TokenResponse,
    UserResponse,
    CheckUserProvidersRequest,
    UserProvidersResponse,
    AddPasswordRequest,
    CheckPhoneRequest,
    PhoneAvailabilityResponse,
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
        # Update phone if from Firebase phone auth and verified
        if phone and not user.phone:
            user.phone = phone
            user.is_phone_verified = True  # Firebase phone auth means verified
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
            is_phone_verified=bool(phone),  # If phone from Firebase auth, it's verified
            migration_status="native",
        )
        db.add(user)
        await db.flush()
        db.add(UserProfile(user_id=user.id))
        
        # Send welcome email for new users
        if email:
            from app.tasks.notifications import send_email_notification
            send_email_notification.delay(
                email,
                "Welcome to Hermes!",
                "email/welcome.html",
                {
                    "name": name,
                    "base_url": settings.FRONTEND_URL or "http://localhost:5000"
                }
            )

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


@router.post("/check-user-providers")
@limiter.limit("10/minute")
async def check_user_providers(request: Request, body: CheckUserProvidersRequest):
    """Check which authentication providers (Google, email/password) a user has."""
    from app.firebase import init_firebase
    if not init_firebase():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Firebase not configured")
    
    import firebase_admin
    from firebase_admin import auth as fb_auth
    
    try:
        user_record = fb_auth.get_user_by_email(body.email)
        
        # Extract provider IDs
        providers = [p.provider_id for p in user_record.provider_data]
        has_password = "password" in providers
        
        # Can add password if account exists with only social providers
        can_add_password = len(providers) > 0 and not has_password
        
        return UserProvidersResponse(
            exists=True,
            has_password=has_password,
            providers=[p.replace(".com", "") for p in providers],  # ["google", "password"]
            can_add_password=can_add_password,
        )
    except firebase_admin.auth.UserNotFoundError:
        return UserProvidersResponse(exists=False)
    except Exception as exc:
        logger.error("check_providers_failed", extra={"email": body.email, "error": str(exc)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to check user")


@router.post("/check-phone-availability", response_model=PhoneAvailabilityResponse)
async def check_phone_availability(
    body: CheckPhoneRequest,
    db: AsyncSession = Depends(get_db),
):
    """Check if phone number is already registered and verified."""
    result = await db.execute(
        select(User).where(
            User.phone == body.phone,
            User.is_phone_verified == True
        )
    )
    user = result.scalar_one_or_none()
    
    if user:
        return PhoneAvailabilityResponse(
            available=False,
            message="This number is already registered. Please sign in.",
            registered=True
        )
    
    return PhoneAvailabilityResponse(
        available=True,
        message="Phone number available for registration",
        registered=False
    )


@router.post("/add-password")
async def add_password(
    body: AddPasswordRequest,
    redis=Depends(get_redis),
):
    """Add password to an existing social-auth account (requires OTP verification)."""
    # Verify the verification token (same as complete-registration)
    try:
        payload = jwt.decode(body.verification_token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        if payload.get("purpose") != "email_verified" or payload.get("email") != body.email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid verification token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired verification token")
    
    # Get Firebase user
    from app.firebase import init_firebase
    if not init_firebase():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Firebase not configured")
    
    import firebase_admin
    from firebase_admin import auth as fb_auth
    
    try:
        user_record = fb_auth.get_user_by_email(body.email)
        providers = [p.provider_id for p in user_record.provider_data]
        
        # Check if password already exists
        if "password" in providers:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password already set for this account")
        
        # Add password to existing account
        fb_auth.update_user(user_record.uid, password=body.password)
        logger.info("password_added_to_account", extra={"email": body.email, "uid": user_record.uid})
        
        # Generate custom token for sign-in
        custom_token = fb_auth.create_custom_token(user_record.uid)
        return FirebaseCustomTokenResponse(custom_token=custom_token.decode())
        
    except firebase_admin.auth.UserNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found")
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("add_password_failed", extra={"email": body.email, "error": str(exc)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add password")


# ─── Email OTP (registration verification) ──────────────────────────────────

# Jinja2 env for email templates
_template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
_jinja_env = Environment(loader=FileSystemLoader(_template_dir), autoescape=True)


def _render_otp_email(otp: str) -> str:
    """Render OTP email template to HTML string."""
    template = _jinja_env.get_template("email/otp.html")
    return template.render(otp=otp)


def _smtp_send_otp(to: str, otp: str) -> None:
    """Send a 6-digit OTP email synchronously. Runs in a thread executor."""
    subject = "Your Hermes verification code"
    html = _render_otp_email(otp)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.MAIL_DEFAULT_SENDER
    msg["To"] = to
    msg.attach(MIMEText(html, "html"))

    if settings.MAIL_USE_TLS:
        server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT, timeout=30)
        server.starttls()
    else:
        server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT, timeout=30)
    if settings.MAIL_USERNAME:
        server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
    server.sendmail(settings.MAIL_DEFAULT_SENDER, to, msg.as_string())
    server.quit()


@router.post("/send-email-otp", response_model=MessageResponse)
@limiter.limit("3/minute")
async def send_email_otp(
    request: Request,
    body: EmailOTPRequest,
    redis=Depends(get_redis),
):
    """Generate a 6-digit OTP, store in Redis with full_name (5 min TTL), and email it."""
    if not settings.MAIL_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service not configured",
        )
    otp = f"{secrets.randbelow(1000000):06d}"
    email_lower = body.email.lower()
    otp_key = f"{settings.REDIS_KEY_PREFIX}:email_otp:{email_lower}"
    data_key = f"{settings.REDIS_KEY_PREFIX}:email_otp_data:{email_lower}"
    
    # Store OTP and registration data (full_name and optional phone)
    import json
    registration_data = {"full_name": body.full_name}
    if body.phone:
        registration_data["phone"] = body.phone
    
    await redis.setex(otp_key, 300, otp)
    await redis.setex(data_key, 300, json.dumps(registration_data))
    
    try:
        await asyncio.to_thread(_smtp_send_otp, body.email, otp)
    except Exception as exc:
        logger.error("otp_email_failed", extra={"email": body.email, "error": str(exc)})
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to send email. Please try again.",
        )
    logger.info("email_otp_sent", extra={"email": body.email})
    return MessageResponse(message="OTP sent to your email")


@router.post("/verify-email-otp", response_model=OTPVerifiedResponse)
@limiter.limit("5/minute")
async def verify_email_otp(
    request: Request,
    body: EmailOTPVerifyRequest,
    redis=Depends(get_redis),
):
    """Verify the 6-digit OTP and return a short-lived verification token."""
    email_lower = body.email.lower()
    otp_key = f"{settings.REDIS_KEY_PREFIX}:email_otp:{email_lower}"
    stored_otp = await redis.get(otp_key)
    
    if not stored_otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP expired or not found")
    if stored_otp.decode() != body.otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

    # Generate verification token (JWT, 5 min TTL)
    verification_token = jwt.encode(
        {
            "email": email_lower,
            "purpose": "email_verified",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        settings.JWT_SECRET_KEY,
        algorithm="HS256",
    )

    # Delete OTP (one-time use)
    await redis.delete(otp_key)
    logger.info("email_otp_verified", extra={"email": body.email})
    return OTPVerifiedResponse(verified=True, verification_token=verification_token)


@router.post("/complete-registration", response_model=FirebaseCustomTokenResponse)
@limiter.limit("5/minute")
async def complete_registration(
    request: Request,
    body: CompleteRegistrationRequest,
    redis=Depends(get_redis),
    db: AsyncSession = Depends(get_db),
):
    """Create Firebase user server-side after email verification, return custom token for sign-in."""
    # Verify the verification token
    try:
        payload = jwt.decode(body.verification_token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        if payload.get("purpose") != "email_verified" or payload.get("email") != body.email.lower():
            raise JWTError("Invalid token purpose or email mismatch")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired verification token")

    # Retrieve stored registration data (full_name and optional phone)
    import json
    email_lower = body.email.lower()
    data_key = f"{settings.REDIS_KEY_PREFIX}:email_otp_data:{email_lower}"
    data_bytes = await redis.get(data_key)
    if not data_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Registration data expired. Please start over.")
    
    try:
        registration_data = json.loads(data_bytes.decode())
        full_name = registration_data.get("full_name")
        stored_phone = registration_data.get("phone")
    except (json.JSONDecodeError, AttributeError):
        # Fallback for old format (just full_name string)
        full_name = data_bytes.decode()
        stored_phone = None
    
    # Use phone from request body if provided, otherwise use stored phone
    phone_number = body.phone or stored_phone

    # Create Firebase user via Admin SDK
    from app.firebase import init_firebase
    if not init_firebase():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Firebase not configured")
    
    import firebase_admin
    from firebase_admin import auth as fb_auth
    
    try:
        # Create user with email_verified=True from the start
        create_params = {
            "email": body.email,
            "password": body.password,
            "display_name": full_name,
            "email_verified": True,
        }
        if phone_number:
            create_params["phone_number"] = phone_number
        
        user_record = fb_auth.create_user(**create_params)
        firebase_uid = user_record.uid
        logger.info("firebase_user_created", extra={"email": body.email, "uid": firebase_uid, "phone": phone_number})
    except firebase_admin.auth.EmailAlreadyExistsError:
        # Email exists in Firebase — sign in instead and check if verified
        try:
            user_record = fb_auth.get_user_by_email(body.email)
            firebase_uid = user_record.uid
            if not user_record.email_verified:
                # Unverified legacy account — update it
                fb_auth.update_user(firebase_uid, email_verified=True, display_name=full_name)
            logger.info("firebase_user_exists", extra={"email": body.email, "uid": firebase_uid})
        except Exception as exc:
            logger.error("firebase_user_lookup_failed", extra={"email": body.email, "error": str(exc)})
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create account")
    except Exception as exc:
        logger.error("firebase_user_creation_failed", extra={"email": body.email, "error": str(exc)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create account")

    # Generate custom token for client-side sign-in
    custom_token = fb_auth.create_custom_token(firebase_uid)
    
    # Send welcome email
    from app.tasks.notifications import send_email_notification
    send_email_notification.delay(
        body.email,
        "Welcome to Hermes!",
        "email/welcome.html",
        {
            "name": full_name or body.email,
            "base_url": settings.FRONTEND_URL or "http://localhost:5000"
        }
    )
    
    # Clean up Redis data
    await redis.delete(data_key)
    
    return FirebaseCustomTokenResponse(custom_token=custom_token.decode())


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
