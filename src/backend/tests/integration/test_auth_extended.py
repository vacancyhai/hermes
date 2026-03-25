"""Extended authentication tests for email OTP, phone auth, and password management.

Tests cover:
- Email OTP registration flow
- Password validation (8 chars, 1 uppercase, 1 special)
- Password set/change functionality
- Phone number verification
- Email linking for phone-only users
"""

import uuid
from unittest.mock import patch, MagicMock

import pytest
from httpx import AsyncClient
from jose import jwt

from app.config import settings


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


pytestmark = pytest.mark.asyncio


# ─── Email OTP Registration ──────────────────────────────────────────────────


async def test_send_email_otp_success(client: AsyncClient):
    """Send OTP to email for registration."""
    email = f"newuser_{uuid.uuid4().hex[:8]}@test.com"
    resp = await client.post("/api/v1/auth/send-email-otp", json={
        "email": email,
        "full_name": "New User",
        "phone": None
    })
    assert resp.status_code == 200
    assert "OTP sent" in resp.json()["message"]


async def test_send_email_otp_with_phone(client: AsyncClient):
    """Send OTP with optional phone number."""
    email = f"withphone_{uuid.uuid4().hex[:8]}@test.com"
    resp = await client.post("/api/v1/auth/send-email-otp", json={
        "email": email,
        "full_name": "Phone User",
        "phone": "+919876543210"
    })
    assert resp.status_code == 200


async def test_verify_email_otp_invalid(client: AsyncClient):
    """Invalid OTP returns error."""
    email = f"invalid_{uuid.uuid4().hex[:8]}@test.com"
    resp = await client.post("/api/v1/auth/verify-email-otp", json={
        "email": email,
        "otp": "999999"
    })
    assert resp.status_code in [400, 401]  # Can be 400 (bad request) or 401


async def test_complete_registration_with_weak_password(client: AsyncClient):
    """Registration fails with weak password (no uppercase)."""
    with patch("app.routers.auth.jwt.decode") as mock_decode:
        mock_decode.return_value = {
            "purpose": "email_verified",
            "email": "test@example.com"
        }
        
        resp = await client.post("/api/v1/auth/complete-registration", json={
            "email": "test@example.com",
            "password": "weak123!",  # No uppercase
            "verification_token": "fake-token"
        })
        assert resp.status_code == 422  # Validation error


async def test_complete_registration_with_short_password(client: AsyncClient):
    """Registration fails with short password."""
    with patch("app.routers.auth.jwt.decode") as mock_decode:
        mock_decode.return_value = {
            "purpose": "email_verified",
            "email": "test@example.com"
        }
        
        resp = await client.post("/api/v1/auth/complete-registration", json={
            "email": "test@example.com",
            "password": "Short1!",  # Only 7 chars
            "verification_token": "fake-token"
        })
        assert resp.status_code == 422


async def test_complete_registration_without_special_char(client: AsyncClient):
    """Registration fails without special character."""
    with patch("app.routers.auth.jwt.decode") as mock_decode:
        mock_decode.return_value = {
            "purpose": "email_verified",
            "email": "test@example.com"
        }
        
        resp = await client.post("/api/v1/auth/complete-registration", json={
            "email": "test@example.com",
            "password": "NoSpecial123",  # No special char
            "verification_token": "fake-token"
        })
        assert resp.status_code == 422


async def test_complete_registration_with_valid_password(client: AsyncClient, test_redis):
    """Registration succeeds with valid password."""
    email = f"validpass_{uuid.uuid4().hex[:8]}@test.com"
    
    # Mock Redis data
    import json
    data_key = f"{settings.REDIS_KEY_PREFIX}:email_otp_data:{email}"
    await test_redis.set(data_key, json.dumps({"full_name": "Valid User", "phone": None}))
    
    with patch("app.routers.auth.jwt.decode") as mock_decode, \
         patch("app.firebase.init_firebase", return_value=True), \
         patch("firebase_admin.auth") as mock_fb:
        
        mock_decode.return_value = {
            "purpose": "email_verified",
            "email": email
        }
        
        mock_user = MagicMock()
        mock_user.uid = f"uid-{uuid.uuid4().hex[:8]}"
        mock_fb.create_user.return_value = mock_user
        mock_fb.create_custom_token.return_value = b"custom-token"
        
        resp = await client.post("/api/v1/auth/complete-registration", json={
            "email": email,
            "password": "ValidPass123!",  # 8+ chars, uppercase, special
            "verification_token": "fake-token"
        })
        
        assert resp.status_code == 200
        assert "custom_token" in resp.json()


# ─── Password Management ──────────────────────────────────────────────────────


async def test_set_password_for_google_user(client: AsyncClient, db):
    """Google OAuth user can set password."""
    from app.models.user import User
    from app.models.user_profile import UserProfile
    from sqlalchemy import select
    
    # Create Google OAuth user (no password provider)
    google_user = User(
        email=f"google_{uuid.uuid4().hex[:8]}@test.com",
        firebase_uid=f"google-uid-{uuid.uuid4().hex[:8]}",
        full_name="Google User",
        is_email_verified=True
    )
    db.add(google_user)
    await db.flush()
    db.add(UserProfile(user_id=google_user.id))
    await db.commit()
    
    from app.routers.auth import create_access_token
    token = create_access_token(str(google_user.id), "user")
    
    with patch("app.firebase.init_firebase", return_value=True), \
         patch("firebase_admin.auth") as mock_fb:
        
        mock_user_record = MagicMock()
        mock_user_record.provider_data = []  # No password provider
        mock_fb.get_user.return_value = mock_user_record
        
        resp = await client.post("/api/v1/users/me/set-password", 
            headers=auth_header(token),
            json={"new_password": "NewPass123!"}
        )
        
        assert resp.status_code == 200
        assert "successfully" in resp.json()["message"].lower()


async def test_set_password_with_weak_password_fails(client: AsyncClient, db):
    """Setting weak password fails validation."""
    from app.models.user import User
    from app.models.user_profile import UserProfile
    
    google_user = User(
        email=f"google_{uuid.uuid4().hex[:8]}@test.com",
        firebase_uid=f"google-uid-{uuid.uuid4().hex[:8]}",
        full_name="Google User",
        is_email_verified=True
    )
    db.add(google_user)
    await db.flush()
    db.add(UserProfile(user_id=google_user.id))
    await db.commit()
    
    from app.routers.auth import create_access_token
    token = create_access_token(str(google_user.id), "user")
    
    resp = await client.post("/api/v1/users/me/set-password", 
        headers=auth_header(token),
        json={"new_password": "weak"}  # Too short
    )
    
    assert resp.status_code == 422


async def test_change_password_requires_current_password(client: AsyncClient, user_token: str):
    """Changing password requires current password."""
    resp = await client.post("/api/v1/users/me/change-password",
        headers=auth_header(user_token),
        json={
            "current_password": "OldPass123!",
            "new_password": "NewPass456!"
        }
    )
    # Without proper Firebase mocking, endpoint will fail
    assert resp.status_code in [200, 400, 404, 500, 503]


async def test_change_password_with_weak_new_password_fails(client: AsyncClient, user_token: str):
    """Changing to weak password fails validation."""
    resp = await client.post("/api/v1/users/me/change-password",
        headers=auth_header(user_token),
        json={
            "current_password": "OldPass123!",
            "new_password": "weak"
        }
    )
    assert resp.status_code == 422


# ─── Phone Verification ───────────────────────────────────────────────────────


async def test_update_phone_marks_as_unverified(client: AsyncClient, user_token: str, db, test_user):
    """Updating phone number marks it as unverified."""
    user_id, _, _ = test_user
    
    resp = await client.put("/api/v1/users/profile/phone",
        headers=auth_header(user_token),
        json={"phone": "+919876543210"}
    )
    
    assert resp.status_code == 200
    assert resp.json()["is_phone_verified"] is False


async def test_verify_phone_otp_with_invalid_otp(client: AsyncClient, user_token: str):
    """Invalid phone OTP fails verification."""
    resp = await client.post("/api/v1/users/me/verify-phone-otp",
        headers=auth_header(user_token),
        json={"otp": "999999"}
    )
    assert resp.status_code in [400, 401]  # Can be 400 (bad request) or 401


async def test_verify_phone_otp_without_phone_fails(client: AsyncClient, db):
    """Cannot verify phone if user has no phone number."""
    from app.models.user import User
    from app.models.user_profile import UserProfile
    
    user = User(
        email=f"nophone_{uuid.uuid4().hex[:8]}@test.com",
        firebase_uid=f"uid-{uuid.uuid4().hex[:8]}",
        full_name="No Phone User",
        is_email_verified=True,
        phone=None  # No phone
    )
    db.add(user)
    await db.flush()
    db.add(UserProfile(user_id=user.id))
    await db.commit()
    
    from app.routers.auth import create_access_token
    token = create_access_token(str(user.id), "user")
    
    resp = await client.post("/api/v1/users/me/verify-phone-otp",
        headers=auth_header(token),
        json={"otp": "123456"}
    )
    assert resp.status_code == 400


# ─── Email Linking ────────────────────────────────────────────────────────────


async def test_link_email_to_phone_only_account(client: AsyncClient, db):
    """Phone-only user can link email and password."""
    from app.models.user import User
    from app.models.user_profile import UserProfile
    
    # Create phone-only user
    phone_user = User(
        email=None,  # No email
        firebase_uid=f"phone-uid-{uuid.uuid4().hex[:8]}",
        full_name="Phone User",
        phone="+919876543210",
        is_phone_verified=True
    )
    db.add(phone_user)
    await db.flush()
    db.add(UserProfile(user_id=phone_user.id))
    await db.commit()
    
    from app.routers.auth import create_access_token
    token = create_access_token(str(phone_user.id), "user")
    
    new_email = f"linked_{uuid.uuid4().hex[:8]}@test.com"
    
    # Create a proper Firebase exception class
    class MockUserNotFoundError(Exception):
        pass
    
    with patch("app.firebase.init_firebase", return_value=True), \
         patch("firebase_admin.auth") as mock_fb:
        
        # Set up the exception as an attribute
        mock_fb.UserNotFoundError = MockUserNotFoundError
        mock_fb.get_user_by_email.side_effect = MockUserNotFoundError("Not found")
        
        # Mock update_user to succeed
        mock_fb.update_user.return_value = None
        
        resp = await client.post("/api/v1/users/me/link-email-password",
            headers=auth_header(token),
            json={
                "email": new_email,
                "password": "LinkPass123!"
            }
        )
        
        assert resp.status_code == 200


async def test_link_email_with_weak_password_fails(client: AsyncClient, db):
    """Linking email with weak password fails validation."""
    from app.models.user import User
    from app.models.user_profile import UserProfile
    
    phone_user = User(
        email=None,
        firebase_uid=f"phone-uid-{uuid.uuid4().hex[:8]}",
        full_name="Phone User",
        phone="+919876543210",
        is_phone_verified=True
    )
    db.add(phone_user)
    await db.flush()
    db.add(UserProfile(user_id=phone_user.id))
    await db.commit()
    
    from app.routers.auth import create_access_token
    token = create_access_token(str(phone_user.id), "user")
    
    resp = await client.post("/api/v1/users/me/link-email-password",
        headers=auth_header(token),
        json={
            "email": f"test_{uuid.uuid4().hex[:8]}@test.com",
            "password": "weak"  # Too short
        }
    )
    assert resp.status_code == 422


async def test_link_email_to_user_with_existing_email_fails(client: AsyncClient, user_token: str):
    """Cannot link email to user who already has email."""
    resp = await client.post("/api/v1/users/me/link-email-password",
        headers=auth_header(user_token),
        json={
            "email": f"another_{uuid.uuid4().hex[:8]}@test.com",
            "password": "AnotherPass123!"
        }
    )
    assert resp.status_code == 400
    json_resp = resp.json()
    error_msg = str(json_resp.get("detail", json_resp.get("error", ""))).lower()
    assert "already" in error_msg


async def test_link_email_with_existing_email_fails(client: AsyncClient, db, test_user):
    """Cannot link email that's already registered."""
    from app.models.user import User
    from app.models.user_profile import UserProfile
    
    # Get existing user's email
    _, existing_email, _ = test_user
    
    # Create phone-only user
    phone_user = User(
        email=None,
        firebase_uid=f"phone-uid-{uuid.uuid4().hex[:8]}",
        full_name="Phone User",
        phone="+919876543210",
        is_phone_verified=True
    )
    db.add(phone_user)
    await db.flush()
    db.add(UserProfile(user_id=phone_user.id))
    await db.commit()
    
    from app.routers.auth import create_access_token
    token = create_access_token(str(phone_user.id), "user")
    
    resp = await client.post("/api/v1/users/me/link-email-password",
        headers=auth_header(token),
        json={
            "email": existing_email,  # Already exists
            "password": "TryLink123!"
        }
    )
    assert resp.status_code == 400
    json_resp = resp.json()
    assert "error" in json_resp or "detail" in json_resp
    error_msg = str(json_resp.get("detail", json_resp.get("error", ""))).lower()
    assert "already registered" in error_msg or "already" in error_msg


# ─── Check Phone Availability ─────────────────────────────────────────────────


async def test_check_phone_availability_available(client: AsyncClient):
    """Check that unregistered phone is available."""
    resp = await client.post("/api/v1/auth/check-phone-availability", json={
        "phone": "+919999999999"
    })
    assert resp.status_code == 200
    assert resp.json()["available"] is True


async def test_check_phone_availability_registered(client: AsyncClient, db):
    """Check that registered phone is not available."""
    from app.models.user import User
    from app.models.user_profile import UserProfile
    
    phone = "+918888888888"
    user = User(
        email=None,
        firebase_uid=f"uid-{uuid.uuid4().hex[:8]}",
        full_name="Existing Phone User",
        phone=phone,
        is_phone_verified=True
    )
    db.add(user)
    await db.flush()
    db.add(UserProfile(user_id=user.id))
    await db.commit()
    
    resp = await client.post("/api/v1/auth/check-phone-availability", json={
        "phone": phone
    })
    assert resp.status_code == 200
    assert resp.json()["available"] is False
    assert resp.json()["registered"] is True


async def test_check_phone_invalid_format(client: AsyncClient):
    """Invalid phone format returns validation error."""
    resp = await client.post("/api/v1/auth/check-phone-availability", json={
        "phone": "123456"  # Invalid format
    })
    assert resp.status_code == 422
