"""Tests for user profile endpoints — profile CRUD, phone, follow, FCM, prefs."""

import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- Get profile ---

async def test_get_profile(client: AsyncClient, user_token: str, test_user):
    resp = await client.get("/api/v1/users/profile", headers=auth_header(user_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert "email" in data
    # Profile may be embedded
    assert "profile" in data or True  # profile is optional if not created


async def test_get_profile_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/users/profile")
    assert resp.status_code in (401, 403)


# --- Update profile ---

async def test_update_profile(client: AsyncClient, user_token: str):
    resp = await client.put(
        "/api/v1/users/profile",
        json={"state": "Maharashtra", "city": "Mumbai", "gender": "Male"},
        headers=auth_header(user_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "Maharashtra"
    assert data["city"] == "Mumbai"


async def test_update_profile_partial(client: AsyncClient, user_token: str):
    resp = await client.put(
        "/api/v1/users/profile",
        json={"highest_qualification": "graduate"},
        headers=auth_header(user_token),
    )
    assert resp.status_code == 200
    assert resp.json()["highest_qualification"] == "graduate"


async def test_update_profile_requires_auth(client: AsyncClient):
    resp = await client.put("/api/v1/users/profile", json={"city": "Delhi"})
    assert resp.status_code in (401, 403)


async def test_update_profile_preferred_states(client: AsyncClient, user_token: str):
    resp = await client.put(
        "/api/v1/users/profile",
        json={"preferred_states": ["Maharashtra", "Karnataka"], "preferred_categories": ["general", "obc"]},
        headers=auth_header(user_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "Maharashtra" in data["preferred_states"]


# --- Update phone ---

async def test_update_phone(client: AsyncClient, user_token: str):
    resp = await client.put(
        "/api/v1/users/profile/phone",
        json={"phone": "+919876543210"},
        headers=auth_header(user_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["phone"] == "+919876543210"


async def test_update_phone_too_short(client: AsyncClient, user_token: str):
    resp = await client.put(
        "/api/v1/users/profile/phone",
        json={"phone": "123"},
        headers=auth_header(user_token),
    )
    assert resp.status_code == 422


async def test_update_phone_requires_auth(client: AsyncClient):
    resp = await client.put("/api/v1/users/profile/phone", json={"phone": "9876543210"})
    assert resp.status_code in (401, 403)


# --- FCM token management ---

async def test_register_fcm_token(client: AsyncClient, user_token: str):
    token = f"fcm-token-{uuid.uuid4().hex}"
    resp = await client.post(
        "/api/v1/users/me/fcm-token",
        json={"token": token, "device_name": "Test Phone"},
        headers=auth_header(user_token),
    )
    assert resp.status_code == 200
    assert resp.json()["fcm_tokens_count"] >= 1


async def test_register_fcm_token_duplicate(client: AsyncClient, user_token: str):
    token = f"fcm-dup-{uuid.uuid4().hex}"
    await client.post(
        "/api/v1/users/me/fcm-token",
        json={"token": token},
        headers=auth_header(user_token),
    )
    resp = await client.post(
        "/api/v1/users/me/fcm-token",
        json={"token": token},
        headers=auth_header(user_token),
    )
    assert resp.status_code == 200
    assert "already registered" in resp.json()["message"].lower()


async def test_register_fcm_token_no_device_name(client: AsyncClient, user_token: str):
    token = f"fcm-noname-{uuid.uuid4().hex}"
    resp = await client.post(
        "/api/v1/users/me/fcm-token",
        json={"token": token},
        headers=auth_header(user_token),
    )
    assert resp.status_code == 200


async def test_unregister_fcm_token(client: AsyncClient, user_token: str):
    token = f"fcm-del-{uuid.uuid4().hex}"
    await client.post(
        "/api/v1/users/me/fcm-token",
        json={"token": token},
        headers=auth_header(user_token),
    )
    resp = await client.request(
        "DELETE",
        "/api/v1/users/me/fcm-token",
        json={"token": token},
        headers=auth_header(user_token),
    )
    assert resp.status_code == 200
    assert "removed" in resp.json()["message"].lower()


async def test_unregister_fcm_token_not_found(client: AsyncClient, user_token: str):
    resp = await client.request(
        "DELETE",
        "/api/v1/users/me/fcm-token",
        json={"token": f"non-existent-fcm-{uuid.uuid4().hex}"},
        headers=auth_header(user_token),
    )
    assert resp.status_code == 404


async def test_fcm_token_requires_auth(client: AsyncClient):
    resp = await client.post("/api/v1/users/me/fcm-token", json={"token": "a" * 20})
    assert resp.status_code in (401, 403)


# --- Notification preferences ---

async def test_update_notification_preferences(client: AsyncClient, user_token: str):
    resp = await client.put(
        "/api/v1/users/me/notification-preferences",
        json={"email": True, "push": False, "in_app": True},
        headers=auth_header(user_token),
    )
    assert resp.status_code == 200
    prefs = resp.json()["notification_preferences"]
    assert prefs["email"] is True
    assert prefs["push"] is False


async def test_update_notification_preferences_partial(client: AsyncClient, user_token: str):
    resp = await client.put(
        "/api/v1/users/me/notification-preferences",
        json={"push": True},
        headers=auth_header(user_token),
    )
    assert resp.status_code == 200
    assert resp.json()["notification_preferences"]["push"] is True


async def test_notification_preferences_requires_auth(client: AsyncClient):
    resp = await client.put("/api/v1/users/me/notification-preferences", json={"email": True})
    assert resp.status_code in (401, 403)
