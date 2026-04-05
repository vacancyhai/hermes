"""Direct unit tests for user route handlers with mocked dependencies."""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_current_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.status = "active"
    user.phone = None
    user.is_email_verified = False
    user.created_at = datetime.now(timezone.utc)
    return user, {"user_type": "user"}


def _make_profile(user_id=None):
    p = MagicMock()
    p.id = uuid.uuid4()
    p.user_id = user_id or uuid.uuid4()
    p.date_of_birth = None
    p.gender = None
    p.category = None
    p.is_pwd = False
    p.is_ex_serviceman = False
    p.state = None
    p.city = None
    p.pincode = None
    p.highest_qualification = None
    p.education = {}
    p.notification_preferences = {}
    p.preferred_states = []
    p.preferred_categories = []
    p.followed_organizations = []
    p.fcm_tokens = []
    p.updated_at = datetime.now(timezone.utc)
    return p


# ─── get_profile ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_profile_with_profile():
    from app.routers.users import get_profile

    user, _ = _make_current_user()
    profile = _make_profile(user_id=user.id)

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = profile
    db.execute.return_value = result

    output = await get_profile(current_user=(user, {}), db=db)
    assert "id" in output
    assert "profile" in output


@pytest.mark.asyncio
async def test_get_profile_no_profile():
    from app.routers.users import get_profile

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result

    output = await get_profile(current_user=_make_current_user(), db=db)
    assert "profile" not in output


# ─── update_profile ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_profile_success():
    from app.routers.users import update_profile
    from app.schemas.users import ProfileUpdateRequest

    user, _ = _make_current_user()
    profile = _make_profile(user_id=user.id)

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = profile
    db.execute.return_value = result

    body = ProfileUpdateRequest(state="Delhi", city="New Delhi")
    output = await update_profile(body=body, current_user=(user, {}), db=db)
    assert profile.state == "Delhi"


@pytest.mark.asyncio
async def test_update_profile_not_found():
    from app.routers.users import update_profile
    from app.schemas.users import ProfileUpdateRequest
    from fastapi import HTTPException

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result

    body = ProfileUpdateRequest(state="Delhi")
    with pytest.raises(HTTPException) as exc_info:
        await update_profile(body=body, current_user=_make_current_user(), db=db)
    assert exc_info.value.status_code == 404


# ─── update_phone ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_phone():
    from app.routers.users import update_phone
    from app.schemas.auth import UpdatePhoneRequest

    user, _ = _make_current_user()
    db = AsyncMock()

    body = UpdatePhoneRequest(phone="+919876543210")
    output = await update_phone(body=body, current_user=(user, {}), db=db)
    assert output["phone"] == "+919876543210"
    assert user.phone == "+919876543210"


# ─── register_fcm_token ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_register_fcm_token_success():
    from app.routers.users import register_fcm_token
    from app.schemas.users import FCMTokenRequest

    profile = _make_profile()
    profile.fcm_tokens = []

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = profile
    db.execute.return_value = result

    body = FCMTokenRequest(token="a" * 20, device_name="My Phone")
    output = await register_fcm_token(
        body=body, current_user=_make_current_user(), db=db
    )
    assert output["fcm_tokens_count"] == 1


@pytest.mark.asyncio
async def test_register_fcm_token_duplicate():
    from app.routers.users import register_fcm_token
    from app.schemas.users import FCMTokenRequest

    token_val = "b" * 20
    profile = _make_profile()
    profile.fcm_tokens = [{"token": token_val, "device_name": "Phone"}]

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = profile
    db.execute.return_value = result

    body = FCMTokenRequest(token=token_val)
    output = await register_fcm_token(
        body=body, current_user=_make_current_user(), db=db
    )
    assert "already registered" in output["message"].lower()


@pytest.mark.asyncio
async def test_register_fcm_token_max_devices():
    from app.routers.users import MAX_FCM_TOKENS, register_fcm_token
    from app.schemas.users import FCMTokenRequest
    from fastapi import HTTPException

    profile = _make_profile()
    profile.fcm_tokens = [{"token": f"token_{i}"} for i in range(MAX_FCM_TOKENS)]

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = profile
    db.execute.return_value = result

    body = FCMTokenRequest(token="new-token-" + "x" * 20)
    with pytest.raises(HTTPException) as exc_info:
        await register_fcm_token(body=body, current_user=_make_current_user(), db=db)
    assert exc_info.value.status_code == 400


# ─── unregister_fcm_token ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_unregister_fcm_token_success():
    from app.routers.users import unregister_fcm_token
    from app.schemas.users import FCMTokenDeleteRequest

    token_val = "c" * 20
    profile = _make_profile()
    profile.fcm_tokens = [{"token": token_val}]

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = profile
    db.execute.return_value = result

    body = FCMTokenDeleteRequest(token=token_val)
    output = await unregister_fcm_token(
        body=body, current_user=_make_current_user(), db=db
    )
    assert output["fcm_tokens_count"] == 0


@pytest.mark.asyncio
async def test_unregister_fcm_token_not_found():
    from app.routers.users import unregister_fcm_token
    from app.schemas.users import FCMTokenDeleteRequest
    from fastapi import HTTPException

    profile = _make_profile()
    profile.fcm_tokens = []

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = profile
    db.execute.return_value = result

    body = FCMTokenDeleteRequest(token="d" * 20)
    with pytest.raises(HTTPException) as exc_info:
        await unregister_fcm_token(body=body, current_user=_make_current_user(), db=db)
    assert exc_info.value.status_code == 404


# ─── update_notification_preferences ─────────────────────────────────────────


@pytest.mark.asyncio
async def test_update_notification_preferences_success():
    from app.routers.users import update_notification_preferences
    from app.schemas.users import NotificationPreferencesRequest

    profile = _make_profile()
    profile.notification_preferences = {}

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = profile
    db.execute.return_value = result

    body = NotificationPreferencesRequest(email=True, push=False)
    output = await update_notification_preferences(
        body=body, current_user=_make_current_user(), db=db
    )
    assert output["notification_preferences"]["email"] is True
    assert output["notification_preferences"]["push"] is False


@pytest.mark.asyncio
async def test_update_notification_preferences_not_found():
    from app.routers.users import update_notification_preferences
    from app.schemas.users import NotificationPreferencesRequest
    from fastapi import HTTPException

    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    db.execute.return_value = result

    body = NotificationPreferencesRequest(email=True)
    with pytest.raises(HTTPException) as exc_info:
        await update_notification_preferences(
            body=body, current_user=_make_current_user(), db=db
        )
    assert exc_info.value.status_code == 404
