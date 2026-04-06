"""Unit tests for auth route handlers with mocked dependencies."""

import json
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from jose import jwt

# ─── helpers ──────────────────────────────────────────────────────────────────


def _make_user(status="active"):
    u = MagicMock()
    u.id = uuid.uuid4()
    u.email = "user@example.com"
    u.full_name = "Test User"
    u.status = status
    u.firebase_uid = "uid-123"
    u.phone = None
    u.is_email_verified = True
    u.is_phone_verified = False
    u.last_login = None
    u.migration_status = "native"
    return u


def _make_admin(status="active", role="admin"):
    a = MagicMock()
    a.id = uuid.uuid4()
    a.email = "admin@example.com"
    a.role = role
    a.status = status
    a.password_hash = "$2b$12$dummyhashvalue000000000000000000000000000000000"
    a.last_login = None
    return a


def _make_request():
    req = MagicMock()
    req.client.host = "127.0.0.1"
    req.headers.get = MagicMock(return_value="pytest-agent")
    return req


def _make_db_result(obj):
    result = MagicMock()
    result.scalar_one_or_none.return_value = obj
    return result


def _make_valid_refresh_token(user_id: str, user_type: str = "user", role=None):
    from app.routers.auth import create_refresh_token

    return create_refresh_token(user_id, user_type, role)


def _make_valid_access_token(user_id: str, user_type: str = "user", role=None):
    from app.routers.auth import create_access_token

    return create_access_token(user_id, user_type, role)


# ─── helper functions ─────────────────────────────────────────────────────────


def test_create_access_token_contains_expected_claims():
    from app.config import settings
    from app.routers.auth import create_access_token
    from app.utils import ALGORITHM

    user_id = str(uuid.uuid4())
    token = create_access_token(user_id, "user")
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == user_id
    assert payload["type"] == "access"
    assert payload["user_type"] == "user"
    assert "jti" in payload


def test_create_refresh_token_contains_expected_claims():
    from app.config import settings
    from app.routers.auth import create_refresh_token
    from app.utils import ALGORITHM

    user_id = str(uuid.uuid4())
    token = create_refresh_token(user_id, "admin", "superadmin")
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == user_id
    assert payload["type"] == "refresh"
    assert payload["user_type"] == "admin"
    assert payload["role"] == "superadmin"


@pytest.mark.asyncio
async def test_blocklist_jti_stores_key():
    from app.routers.auth import _blocklist_jti

    redis = AsyncMock()
    jti = str(uuid.uuid4())
    exp = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
    await _blocklist_jti(redis, jti, exp)
    redis.setex.assert_called_once()
    call_args = redis.setex.call_args[0]
    assert jti in call_args[0]


@pytest.mark.asyncio
async def test_blocklist_jti_skips_none_jti():
    from app.routers.auth import _blocklist_jti

    redis = AsyncMock()
    await _blocklist_jti(redis, None, 9999999999)
    redis.setex.assert_not_called()


def test_validate_user_status_active_passes():
    from app.routers.auth import _validate_user_status

    user = _make_user(status="active")
    _validate_user_status(user)  # should not raise


def test_validate_user_status_suspended_raises():
    from app.routers.auth import _validate_user_status

    user = _make_user(status="suspended")
    with pytest.raises(HTTPException) as exc_info:
        _validate_user_status(user)
    assert exc_info.value.status_code == 403


def test_validate_user_status_deleted_raises():
    from app.routers.auth import _validate_user_status

    user = _make_user(status="deleted")
    with pytest.raises(HTTPException) as exc_info:
        _validate_user_status(user)
    assert exc_info.value.status_code == 401


def test_update_user_from_firebase_syncs_fields():
    from app.routers.auth import _update_user_from_firebase

    user = _make_user()
    user.is_email_verified = False
    user.phone = None
    user.email = None

    _update_user_from_firebase(user, "new@example.com", True, "+911234567890")

    assert user.is_email_verified is True
    assert user.phone == "+911234567890"
    assert user.is_phone_verified is True
    assert user.email == "new@example.com"


def test_update_user_from_firebase_does_not_overwrite_existing():
    from app.routers.auth import _update_user_from_firebase

    user = _make_user()
    user.is_email_verified = True
    user.phone = "+910000000000"

    _update_user_from_firebase(user, "other@example.com", True, "+911111111111")

    assert user.phone == "+910000000000"  # not overwritten


# ─── _find_user_by_uid_or_email ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_find_user_by_uid_found():
    from app.routers.auth import _find_user_by_uid_or_email

    db = AsyncMock()
    user = _make_user()
    db.execute.return_value = _make_db_result(user)

    result = await _find_user_by_uid_or_email(db, "uid-123", "user@example.com")
    assert result is user


@pytest.mark.asyncio
async def test_find_user_by_email_fallback():
    from app.routers.auth import _find_user_by_uid_or_email

    db = AsyncMock()
    user = _make_user()
    # First call (by uid) returns None, second call (by email) returns user
    db.execute.side_effect = [_make_db_result(None), _make_db_result(user)]

    result = await _find_user_by_uid_or_email(db, "new-uid", "user@example.com")
    assert result is user
    assert user.firebase_uid == "new-uid"
    assert user.migration_status == "migrated"


# ─── logout ───────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_logout_blocklists_access_token_jti():
    from app.routers.auth import logout
    from app.schemas.auth import LogoutRequest

    user = _make_user()
    jti = str(uuid.uuid4())
    exp = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
    redis = AsyncMock()
    body = LogoutRequest()

    await logout(
        current_user=(user, {"jti": jti, "exp": exp}),
        redis=redis,
        body=body,
    )

    redis.setex.assert_called_once()
    assert jti in redis.setex.call_args[0][0]


@pytest.mark.asyncio
async def test_logout_with_refresh_token_blocklists_both():
    from app.routers.auth import logout
    from app.schemas.auth import LogoutRequest

    user = _make_user()
    user_id = str(user.id)
    access_jti = str(uuid.uuid4())
    exp = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
    redis = AsyncMock()

    refresh_token = _make_valid_refresh_token(user_id, "user")
    body = LogoutRequest(refresh_token=refresh_token)

    await logout(
        current_user=(user, {"jti": access_jti, "exp": exp}),
        redis=redis,
        body=body,
    )

    assert redis.setex.call_count == 2


# ─── refresh ──────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_refresh_returns_new_tokens():
    from app.routers.auth import refresh
    from app.schemas.auth import RefreshRequest

    user = _make_user()
    user_id = str(user.id)
    db = AsyncMock()
    redis = AsyncMock()
    redis.get.return_value = None  # not blocklisted
    db.execute.return_value = _make_db_result(user)

    token = _make_valid_refresh_token(user_id, "user")
    body = RefreshRequest(refresh_token=token)

    result = await refresh(body=body, db=db, redis=redis)
    assert result.access_token
    assert result.refresh_token


@pytest.mark.asyncio
async def test_refresh_invalid_token_raises_401():
    from app.routers.auth import refresh
    from app.schemas.auth import RefreshRequest

    db = AsyncMock()
    redis = AsyncMock()
    body = RefreshRequest(refresh_token="not.a.valid.token")

    with pytest.raises(HTTPException) as exc_info:
        await refresh(body=body, db=db, redis=redis)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_refresh_wrong_token_type_raises_401():
    from app.routers.auth import refresh
    from app.schemas.auth import RefreshRequest

    user = _make_user()
    db = AsyncMock()
    redis = AsyncMock()
    # Pass an access token (type=access) instead of a refresh token
    token = _make_valid_access_token(str(user.id), "user")
    body = RefreshRequest(refresh_token=token)

    with pytest.raises(HTTPException) as exc_info:
        await refresh(body=body, db=db, redis=redis)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_refresh_blocklisted_token_raises_401():
    from app.routers.auth import refresh
    from app.schemas.auth import RefreshRequest

    user = _make_user()
    db = AsyncMock()
    redis = AsyncMock()
    redis.get.return_value = b"1"  # blocklisted

    token = _make_valid_refresh_token(str(user.id), "user")
    body = RefreshRequest(refresh_token=token)

    with pytest.raises(HTTPException) as exc_info:
        await refresh(body=body, db=db, redis=redis)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_refresh_inactive_user_raises_401():
    from app.routers.auth import refresh
    from app.schemas.auth import RefreshRequest

    user = _make_user(status="suspended")
    user_id = str(user.id)
    db = AsyncMock()
    redis = AsyncMock()
    redis.get.return_value = None
    db.execute.return_value = _make_db_result(user)

    token = _make_valid_refresh_token(user_id, "user")
    body = RefreshRequest(refresh_token=token)

    with pytest.raises(HTTPException) as exc_info:
        await refresh(body=body, db=db, redis=redis)
    assert exc_info.value.status_code == 401


# ─── check_phone_availability ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_check_phone_available():
    from app.routers.auth import check_phone_availability
    from app.schemas.auth import CheckPhoneRequest

    db = AsyncMock()
    db.execute.return_value = _make_db_result(None)

    body = CheckPhoneRequest(phone="+911234567890")
    result = await check_phone_availability(body=body, db=db)
    assert result.available is True
    assert result.registered is False


@pytest.mark.asyncio
async def test_check_phone_already_registered():
    from app.routers.auth import check_phone_availability
    from app.schemas.auth import CheckPhoneRequest

    db = AsyncMock()
    user = _make_user()
    db.execute.return_value = _make_db_result(user)

    body = CheckPhoneRequest(phone="+911234567890")
    result = await check_phone_availability(body=body, db=db)
    assert result.available is False
    assert result.registered is True


# ─── send_email_otp ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_send_email_otp_mail_disabled_raises_503():
    from app.routers.auth import send_email_otp
    from app.schemas.auth import EmailOTPRequest

    redis = AsyncMock()
    req = _make_request()
    body = EmailOTPRequest(email="user@example.com", full_name="Test")

    with patch("app.routers.auth.settings") as mock_settings:
        mock_settings.MAIL_ENABLED = False
        mock_settings.REDIS_KEY_PREFIX = "hermes"
        with pytest.raises(HTTPException) as exc_info:
            await send_email_otp(request=req, body=body, redis=redis)
    assert exc_info.value.status_code == 503


@pytest.mark.asyncio
async def test_send_email_otp_success():
    from app.routers.auth import send_email_otp
    from app.schemas.auth import EmailOTPRequest

    redis = AsyncMock()
    req = _make_request()
    body = EmailOTPRequest(email="user@example.com", full_name="Test User")

    with patch("app.routers.auth.settings") as mock_settings:
        mock_settings.MAIL_ENABLED = True
        mock_settings.REDIS_KEY_PREFIX = "hermes"
        mock_settings.MAIL_DEFAULT_SENDER = "noreply@example.com"
        mock_settings.MAIL_SERVER = "smtp.example.com"
        mock_settings.MAIL_PORT = 587
        mock_settings.MAIL_USE_TLS = True
        mock_settings.MAIL_USERNAME = ""
        mock_settings.MAIL_PASSWORD = ""
        with patch("app.routers.auth.asyncio.to_thread", new=AsyncMock()):
            result = await send_email_otp(request=req, body=body, redis=redis)

    assert result.message == "OTP sent to your email"
    assert redis.setex.call_count == 2


@pytest.mark.asyncio
async def test_send_email_otp_smtp_failure_raises_502():
    from app.routers.auth import send_email_otp
    from app.schemas.auth import EmailOTPRequest

    redis = AsyncMock()
    req = _make_request()
    body = EmailOTPRequest(email="user@example.com", full_name="Test")

    with patch("app.routers.auth.settings") as mock_settings:
        mock_settings.MAIL_ENABLED = True
        mock_settings.REDIS_KEY_PREFIX = "hermes"
        with patch(
            "app.routers.auth.asyncio.to_thread", side_effect=Exception("SMTP down")
        ):
            with pytest.raises(HTTPException) as exc_info:
                await send_email_otp(request=req, body=body, redis=redis)
    assert exc_info.value.status_code == 502


# ─── verify_email_otp ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_verify_email_otp_success():
    from app.routers.auth import verify_email_otp
    from app.schemas.auth import EmailOTPVerifyRequest

    redis = AsyncMock()
    redis.get.return_value = b"123456"
    req = _make_request()
    body = EmailOTPVerifyRequest(email="user@example.com", otp="123456")

    result = await verify_email_otp(request=req, body=body, redis=redis)
    assert result.verified is True
    assert result.verification_token
    redis.delete.assert_called_once()


@pytest.mark.asyncio
async def test_verify_email_otp_expired_raises_400():
    from app.routers.auth import verify_email_otp
    from app.schemas.auth import EmailOTPVerifyRequest

    redis = AsyncMock()
    redis.get.return_value = None
    req = _make_request()
    body = EmailOTPVerifyRequest(email="user@example.com", otp="123456")

    with pytest.raises(HTTPException) as exc_info:
        await verify_email_otp(request=req, body=body, redis=redis)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_verify_email_otp_wrong_otp_raises_400():
    from app.routers.auth import verify_email_otp
    from app.schemas.auth import EmailOTPVerifyRequest

    redis = AsyncMock()
    redis.get.return_value = b"654321"
    req = _make_request()
    body = EmailOTPVerifyRequest(email="user@example.com", otp="000000")

    with pytest.raises(HTTPException) as exc_info:
        await verify_email_otp(request=req, body=body, redis=redis)
    assert exc_info.value.status_code == 400


# ─── admin_login ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_login_success():
    from app.routers.auth import admin_login
    from app.schemas.auth import AdminLoginRequest

    admin = _make_admin()
    db = AsyncMock()
    db.execute.return_value = _make_db_result(admin)
    req = _make_request()
    body = AdminLoginRequest(email="admin@example.com", password="correct-password")

    with patch("app.routers.auth.pwd_context") as mock_pwd:
        mock_pwd.verify.return_value = True
        result = await admin_login(request=req, body=body, db=db)

    assert result.access_token
    assert result.refresh_token
    db.add.assert_called_once()  # AdminLog added


@pytest.mark.asyncio
async def test_admin_login_wrong_password_raises_401():
    from app.routers.auth import admin_login
    from app.schemas.auth import AdminLoginRequest

    admin = _make_admin()
    db = AsyncMock()
    db.execute.return_value = _make_db_result(admin)
    req = _make_request()
    body = AdminLoginRequest(email="admin@example.com", password="wrong")

    with patch("app.routers.auth.pwd_context") as mock_pwd:
        mock_pwd.verify.return_value = False
        with pytest.raises(HTTPException) as exc_info:
            await admin_login(request=req, body=body, db=db)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_admin_login_not_found_raises_401():
    from app.routers.auth import admin_login
    from app.schemas.auth import AdminLoginRequest

    db = AsyncMock()
    db.execute.return_value = _make_db_result(None)
    req = _make_request()
    body = AdminLoginRequest(email="nobody@example.com", password="pass")

    with patch("app.routers.auth.pwd_context") as mock_pwd:
        mock_pwd.verify.return_value = False
        with pytest.raises(HTTPException) as exc_info:
            await admin_login(request=req, body=body, db=db)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_admin_login_suspended_raises_403():
    from app.routers.auth import admin_login
    from app.schemas.auth import AdminLoginRequest

    admin = _make_admin(status="suspended")
    db = AsyncMock()
    db.execute.return_value = _make_db_result(admin)
    req = _make_request()
    body = AdminLoginRequest(email="admin@example.com", password="pass")

    with patch("app.routers.auth.pwd_context") as mock_pwd:
        mock_pwd.verify.return_value = True
        with pytest.raises(HTTPException) as exc_info:
            await admin_login(request=req, body=body, db=db)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_admin_login_deleted_raises_401():
    from app.routers.auth import admin_login
    from app.schemas.auth import AdminLoginRequest

    admin = _make_admin(status="deleted")
    db = AsyncMock()
    db.execute.return_value = _make_db_result(admin)
    req = _make_request()
    body = AdminLoginRequest(email="admin@example.com", password="pass")

    with patch("app.routers.auth.pwd_context") as mock_pwd:
        mock_pwd.verify.return_value = True
        with pytest.raises(HTTPException) as exc_info:
            await admin_login(request=req, body=body, db=db)
    assert exc_info.value.status_code == 401


# ─── admin_logout ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_logout_blocklists_jti():
    from app.routers.auth import admin_logout
    from app.schemas.auth import LogoutRequest

    admin = _make_admin()
    jti = str(uuid.uuid4())
    exp = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
    redis = AsyncMock()
    db = AsyncMock()
    req = _make_request()
    body = LogoutRequest()

    await admin_logout(
        request=req,
        current_admin=(admin, {"jti": jti, "exp": exp}),
        redis=redis,
        db=db,
        body=body,
    )

    redis.setex.assert_called_once()
    db.add.assert_called_once()  # AdminLog


@pytest.mark.asyncio
async def test_admin_logout_with_refresh_token_blocklists_both():
    from app.routers.auth import admin_logout
    from app.schemas.auth import LogoutRequest

    admin = _make_admin()
    access_jti = str(uuid.uuid4())
    exp = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
    redis = AsyncMock()
    db = AsyncMock()
    req = _make_request()

    refresh_token = _make_valid_refresh_token(str(admin.id), "admin", "admin")
    body = LogoutRequest(refresh_token=refresh_token)

    await admin_logout(
        request=req,
        current_admin=(admin, {"jti": access_jti, "exp": exp}),
        redis=redis,
        db=db,
        body=body,
    )

    assert redis.setex.call_count == 2


# ─── admin_refresh ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_refresh_success():
    from app.routers.auth import admin_refresh
    from app.schemas.auth import RefreshRequest

    admin = _make_admin()
    admin_id = str(admin.id)
    db = AsyncMock()
    redis = AsyncMock()
    redis.get.return_value = None
    db.execute.return_value = _make_db_result(admin)
    req = _make_request()

    token = _make_valid_refresh_token(admin_id, "admin", "admin")
    body = RefreshRequest(refresh_token=token)

    result = await admin_refresh(request=req, body=body, db=db, redis=redis)
    assert result.access_token
    assert result.refresh_token
    db.add.assert_called_once()  # AdminLog


@pytest.mark.asyncio
async def test_admin_refresh_invalid_token_raises_401():
    from app.routers.auth import admin_refresh
    from app.schemas.auth import RefreshRequest

    db = AsyncMock()
    redis = AsyncMock()
    req = _make_request()
    body = RefreshRequest(refresh_token="garbage.token.here")

    with pytest.raises(HTTPException) as exc_info:
        await admin_refresh(request=req, body=body, db=db, redis=redis)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_admin_refresh_user_token_type_rejected():
    from app.routers.auth import admin_refresh
    from app.schemas.auth import RefreshRequest

    admin = _make_admin()
    db = AsyncMock()
    redis = AsyncMock()
    req = _make_request()
    # Pass a user refresh token to the admin endpoint
    token = _make_valid_refresh_token(str(admin.id), "user")
    body = RefreshRequest(refresh_token=token)

    with pytest.raises(HTTPException) as exc_info:
        await admin_refresh(request=req, body=body, db=db, redis=redis)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_admin_refresh_blocklisted_raises_401():
    from app.routers.auth import admin_refresh
    from app.schemas.auth import RefreshRequest

    admin = _make_admin()
    db = AsyncMock()
    redis = AsyncMock()
    redis.get.return_value = b"1"
    req = _make_request()

    token = _make_valid_refresh_token(str(admin.id), "admin", "admin")
    body = RefreshRequest(refresh_token=token)

    with pytest.raises(HTTPException) as exc_info:
        await admin_refresh(request=req, body=body, db=db, redis=redis)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_admin_refresh_inactive_admin_raises_401():
    from app.routers.auth import admin_refresh
    from app.schemas.auth import RefreshRequest

    admin = _make_admin(status="suspended")
    admin_id = str(admin.id)
    db = AsyncMock()
    redis = AsyncMock()
    redis.get.return_value = None
    db.execute.return_value = _make_db_result(admin)
    req = _make_request()

    token = _make_valid_refresh_token(admin_id, "admin", "admin")
    body = RefreshRequest(refresh_token=token)

    with pytest.raises(HTTPException) as exc_info:
        await admin_refresh(request=req, body=body, db=db, redis=redis)
    assert exc_info.value.status_code == 401


# ─── _register_new_firebase_user ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_new_firebase_user_creates_user_and_profile():
    from app.routers.auth import _register_new_firebase_user

    db = AsyncMock()
    db.flush = AsyncMock()

    with patch("app.tasks.notifications.send_email_notification") as mock_task:
        mock_task.delay = MagicMock()
        user = await _register_new_firebase_user(
            db=db,
            email="new@example.com",
            firebase_uid="firebase-uid-999",
            name="New User",
            email_verified=True,
            phone=None,
            provider="google.com",
        )

    db.add.assert_called()
    db.flush.assert_called_once()
    assert user.email == "new@example.com"
    assert user.firebase_uid == "firebase-uid-999"


@pytest.mark.asyncio
async def test_register_new_firebase_user_password_provider_no_email():
    from app.routers.auth import _register_new_firebase_user

    db = AsyncMock()
    db.flush = AsyncMock()

    user = await _register_new_firebase_user(
        db=db,
        email="pw@example.com",
        firebase_uid="uid-pw",
        name="PW User",
        email_verified=True,
        phone=None,
        provider="password",
    )

    # No welcome email for password provider
    assert user.firebase_uid == "uid-pw"
