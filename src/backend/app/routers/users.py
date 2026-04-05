"""User profile endpoints (requires user JWT).

GET    /api/v1/users/profile               — Get own profile
PUT    /api/v1/users/profile               — Update own profile
PUT    /api/v1/users/profile/phone         — Update phone number
POST   /api/v1/users/me/send-phone-otp     — Send OTP to verify phone
POST   /api/v1/users/me/verify-phone-otp   — Verify phone with OTP
POST   /api/v1/users/me/fcm-token          — Register FCM device token
DELETE /api/v1/users/me/fcm-token          — Unregister FCM token
PUT    /api/v1/users/me/notification-preferences — Update notification preferences
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.config import settings
from app.dependencies import get_current_user, get_db
from app.models.user_profile import UserProfile
from app.rate_limit import limiter
from app.schemas.auth import (
    ChangePasswordRequest,
    LinkEmailPasswordRequest,
    MessageResponse,
    SetPasswordRequest,
    UpdatePhoneRequest,
    UserResponse,
    VerifyPhoneRequest,
)
from app.schemas.users import (
    FCMTokenDeleteRequest,
    FCMTokenRequest,
    NotificationPreferencesRequest,
    ProfileResponse,
    ProfileUpdateRequest,
)
from app.utils import MAX_FCM_TOKENS

router = APIRouter(tags=["users"])


@router.get("/api/v1/users/profile")
async def get_profile(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get own user data and profile."""
    user, _ = current_user

    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()

    user_data = UserResponse.model_validate(user).model_dump()
    if profile:
        user_data["profile"] = ProfileResponse.model_validate(profile).model_dump()

    return user_data


@router.put("/api/v1/users/profile")
async def update_profile(
    body: ProfileUpdateRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update own profile fields."""
    user, _ = current_user

    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    logger.info(
        "profile_updated",
        extra={"user_id": str(user.id), "fields": list(update_data.keys())},
    )
    return ProfileResponse.model_validate(profile).model_dump()


@router.put("/api/v1/users/profile/phone")
async def update_phone(
    body: UpdatePhoneRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update phone number on user record. Marks phone as unverified."""
    user, _ = current_user

    # Update phone and mark as unverified
    user.phone = body.phone
    user.is_phone_verified = False

    logger.info("phone_updated", extra={"user_id": str(user.id), "phone": body.phone})

    # Send email notification if user has email
    if user.email:
        from app.tasks.notifications import send_email_notification

        send_email_notification.delay(
            user.email,
            "Phone Number Added to Your Account",
            "email/phone_added.html",
            {
                "name": user.full_name or user.email,
                "email": user.email,
                "phone": body.phone,
                "timestamp": datetime.now(timezone.utc).strftime(
                    "%B %d, %Y at %H:%M UTC"
                ),
                "base_url": settings.FRONTEND_URL or "http://localhost:5000",
            },
        )

    return {
        "message": "Phone number updated. Please verify your new number.",
        "phone": body.phone,
        "is_phone_verified": False,
    }


@router.post("/api/v1/users/me/send-phone-otp", response_model=MessageResponse)
@limiter.limit("3/minute")
async def send_phone_otp(
    request: Request,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Initiate phone verification via Firebase client-side phone auth.

    The client should use the Firebase JS SDK to send an SMS to the user's
    registered phone number, then call POST /verify-phone-otp with the
    resulting Firebase ID token to complete verification server-side.
    """
    user, _ = current_user

    if not user.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No phone number on file. Please update your phone number first.",
        )

    if user.is_phone_verified:
        return MessageResponse(message="Phone number already verified")

    logger.info(
        "phone_otp_requested", extra={"user_id": str(user.id), "phone": user.phone}
    )
    return MessageResponse(
        message="Use Firebase phone auth on the client to verify your number."
    )


@router.post("/api/v1/users/me/verify-phone-otp")
@limiter.limit("5/minute")
async def verify_phone_otp(
    request: Request,
    body: VerifyPhoneRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark the authenticated user's phone as verified.

    Client must complete Firebase phone auth (SMS → OTP entry) and send the
    resulting Firebase ID token. The phone_number claim in the token must
    match the phone number stored on the account.
    """
    user, _ = current_user

    if not user.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No phone number on file"
        )

    from app.firebase import verify_id_token

    try:
        decoded = verify_id_token(body.firebase_id_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Firebase token"
        )

    token_phone = decoded.get("phone_number")
    if not token_phone or token_phone != user.phone:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token phone number does not match account phone number",
        )

    user.is_phone_verified = True
    logger.info("phone_verified", extra={"user_id": str(user.id), "phone": user.phone})

    # Send email notification if user has email
    if user.email:
        from app.tasks.notifications import send_email_notification

        send_email_notification.delay(
            user.email,
            "Phone Number Verified Successfully",
            "email/phone_verified.html",
            {
                "name": user.full_name or user.email,
                "phone": user.phone,
                "timestamp": datetime.now(timezone.utc).strftime(
                    "%B %d, %Y at %H:%M UTC"
                ),
                "base_url": settings.FRONTEND_URL or "http://localhost:5000",
            },
        )

    return {"message": "Phone number verified successfully", "is_phone_verified": True}


# --- Password Management ---


@router.post("/api/v1/users/me/set-password")
@limiter.limit("5/minute")
async def set_password(
    request: Request,
    body: SetPasswordRequest,
    current_user=Depends(get_current_user),
):
    """Set password for Google OAuth users who don't have one."""
    user, _ = current_user

    if not user.firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not linked to Firebase",
        )

    from app.firebase import init_firebase

    if not init_firebase():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase not configured",
        )

    import firebase_admin
    from firebase_admin import auth as fb_auth

    try:
        user_record = fb_auth.get_user(user.firebase_uid)
        providers = [p.provider_id for p in user_record.provider_data]

        # Check if password already exists
        if "password" in providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password already set. Use change password instead.",
            )

        # Add password to Firebase account
        fb_auth.update_user(user.firebase_uid, password=body.new_password)
        logger.info(
            "password_set", extra={"user_id": str(user.id), "uid": user.firebase_uid}
        )

        # Send email notification
        if user.email:
            from app.tasks.notifications import send_email_notification

            send_email_notification.delay(
                user.email,
                "Password Added to Your Account",
                "email/password_set.html",
                {
                    "name": user.full_name or user.email,
                    "email": user.email,
                    "timestamp": datetime.now(timezone.utc).strftime(
                        "%B %d, %Y at %H:%M UTC"
                    ),
                    "original_method": (
                        "Google"
                        if "google.com"
                        in [p.provider_id for p in user_record.provider_data]
                        else "Phone"
                    ),
                    "base_url": settings.FRONTEND_URL or "http://localhost:5000",
                },
            )

        return {
            "message": "Password set successfully. You can now login with email and password."
        }

    except firebase_admin.auth.UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Firebase user not found"
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "set_password_failed", extra={"user_id": str(user.id), "error": str(exc)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set password",
        )


@router.post("/api/v1/users/me/change-password")
@limiter.limit("5/minute")
async def change_password(
    request: Request,
    body: ChangePasswordRequest,
    current_user=Depends(get_current_user),
):
    """Change password for users who already have one. Re-authenticate client-side before calling."""
    user, _ = current_user

    if not user.firebase_uid or not user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not properly configured",
        )

    from app.firebase import init_firebase

    if not init_firebase():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase not configured",
        )

    import firebase_admin
    from firebase_admin import auth as fb_auth

    try:
        user_record = fb_auth.get_user(user.firebase_uid)
        providers = [p.provider_id for p in user_record.provider_data]

        if "password" not in providers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No password set. Use set password instead.",
            )

        # Update password in Firebase
        fb_auth.update_user(user.firebase_uid, password=body.new_password)
        logger.info(
            "password_changed",
            extra={"user_id": str(user.id), "uid": user.firebase_uid},
        )

        # Send email notification
        if user.email:
            from app.tasks.notifications import send_email_notification

            send_email_notification.delay(
                user.email,
                "Password Changed Successfully",
                "email/password_changed.html",
                {
                    "name": user.full_name or user.email,
                    "email": user.email,
                    "timestamp": datetime.now(timezone.utc).strftime(
                        "%B %d, %Y at %H:%M UTC"
                    ),
                    "base_url": settings.FRONTEND_URL or "http://localhost:5000",
                },
            )

        return {"message": "Password changed successfully."}

    except firebase_admin.auth.UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Firebase user not found"
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "change_password_failed", extra={"user_id": str(user.id), "error": str(exc)}
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password",
        )


@router.post("/api/v1/users/me/link-email-password")
@limiter.limit("5/minute")
async def link_email_password(
    request: Request,
    body: LinkEmailPasswordRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Link email+password to phone-only account. Only if email not already registered."""
    user, _ = current_user

    if not user.firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not linked to Firebase",
        )

    # Check if user already has email
    if user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account already has an email address",
        )

    email_lower = body.email.lower()

    # Check if email already exists in PostgreSQL
    from app.models.user import User

    result = await db.execute(select(User).where(User.email == email_lower))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email is already registered. Please use a different email.",
        )

    from app.firebase import init_firebase

    if not init_firebase():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase not configured",
        )

    import firebase_admin
    from firebase_admin import auth as fb_auth

    try:
        # Check if email already exists in Firebase
        try:
            fb_auth.get_user_by_email(body.email)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email is already registered. Please use a different email.",
            )
        except firebase_admin.auth.UserNotFoundError:
            # Email not found in Firebase - good to proceed
            pass

        # Update Firebase user with email and password
        fb_auth.update_user(
            user.firebase_uid,
            email=body.email,
            password=body.password,
            email_verified=False,  # User should verify email
        )

        # Update PostgreSQL user record
        user.email = email_lower
        user.is_email_verified = False

        logger.info(
            "email_password_linked",
            extra={
                "user_id": str(user.id),
                "uid": user.firebase_uid,
                "email": email_lower,
            },
        )

        # Send email notification to newly linked email
        from app.tasks.notifications import send_email_notification

        send_email_notification.delay(
            email_lower,
            "Email Address Linked to Your Account",
            "email/email_linked.html",
            {
                "name": user.full_name or "User",
                "email": email_lower,
                "phone": user.phone,
                "timestamp": datetime.now(timezone.utc).strftime(
                    "%B %d, %Y at %H:%M UTC"
                ),
                "base_url": settings.FRONTEND_URL or "http://localhost:5000",
            },
        )

        return {
            "message": "Email and password added successfully. You can now login with email/password.",
            "email": email_lower,
        }

    except firebase_admin.auth.UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Firebase user not found"
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "link_email_password_failed",
            extra={"user_id": str(user.id), "error": str(exc)},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to link email and password",
        )


# --- FCM Token Management ---


@router.post("/api/v1/users/me/fcm-token")
async def register_fcm_token(
    body: FCMTokenRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register an FCM device token for push notifications. Max 10 devices."""
    user, _ = current_user
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    tokens = list(profile.fcm_tokens or [])

    # Deduplicate by token value
    existing = [
        t for t in tokens if isinstance(t, dict) and t.get("token") == body.token
    ]
    if existing:
        return {"message": "Token already registered", "fcm_tokens_count": len(tokens)}

    if len(tokens) >= MAX_FCM_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {MAX_FCM_TOKENS} devices allowed",
        )

    tokens.append(
        {
            "token": body.token,
            "device_name": body.device_name or "Unknown",
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    profile.fcm_tokens = tokens
    logger.info(
        "fcm_token_registered",
        extra={"user_id": str(user.id), "device_name": body.device_name or "Unknown"},
    )
    return {"message": "FCM token registered", "fcm_tokens_count": len(tokens)}


@router.delete("/api/v1/users/me/fcm-token")
async def unregister_fcm_token(
    body: FCMTokenDeleteRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unregister an FCM device token."""
    user, _ = current_user
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    tokens = list(profile.fcm_tokens or [])
    new_tokens = [
        t for t in tokens if not (isinstance(t, dict) and t.get("token") == body.token)
    ]

    if len(new_tokens) == len(tokens):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Token not found"
        )

    profile.fcm_tokens = new_tokens
    logger.info("fcm_token_removed", extra={"user_id": str(user.id)})
    return {"message": "FCM token removed", "fcm_tokens_count": len(new_tokens)}


# --- Notification Preferences ---


@router.put("/api/v1/users/me/notification-preferences")
async def update_notification_preferences(
    body: NotificationPreferencesRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update notification channel preferences (email, push, in_app)."""
    user, _ = current_user
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
        )

    prefs = dict(profile.notification_preferences or {})
    update_data = body.model_dump(exclude_unset=True)

    # telegram_chat_id is stored nested inside prefs["telegram"] dict
    chat_id = update_data.pop("telegram_chat_id", None)
    if chat_id is not None:
        tg = prefs.get("telegram") if isinstance(prefs.get("telegram"), dict) else {}
        tg["chat_id"] = chat_id
        prefs["telegram"] = tg

    for key, value in update_data.items():
        if key == "telegram" and isinstance(prefs.get("telegram"), dict):
            # Preserve existing chat_id when only toggling enabled/disabled
            prefs["telegram"]["enabled"] = value
        else:
            prefs[key] = value

    profile.notification_preferences = prefs
    logger.info(
        "notification_preferences_updated",
        extra={"user_id": str(user.id), "channels": list(update_data.keys())},
    )
    return {"message": "Preferences updated", "notification_preferences": prefs}
