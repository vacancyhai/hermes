"""Tests for admin endpoints — dashboard, user management, RBAC."""

import uuid

import pytest
from httpx import AsyncClient


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}

pytestmark = pytest.mark.asyncio


async def test_admin_stats(client: AsyncClient, admin_token: str):
    resp = await client.get("/api/v1/admin/stats", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "jobs" in data
    assert "users" in data
    assert "admit_cards" in data
    assert "entrance_exams" in data
    assert "new_this_week" in data["users"]


async def test_admin_list_users(client: AsyncClient, admin_token: str, test_user):
    resp = await client.get("/api/v1/admin/users", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["pagination"]["total"] >= 1


async def test_admin_search_users(client: AsyncClient, admin_token: str, test_user):
    _, email, _ = test_user
    resp = await client.get(f"/api/v1/admin/users?q={email}", headers=auth_header(admin_token))
    assert resp.status_code == 200
    assert resp.json()["pagination"]["total"] >= 1


async def test_admin_get_user_detail(client: AsyncClient, admin_token: str, test_user):
    user_id, _, _ = test_user
    resp = await client.get(f"/api/v1/admin/users/{user_id}", headers=auth_header(admin_token))
    assert resp.status_code == 200
    assert resp.json()["id"] == user_id


async def test_admin_suspend_user(client: AsyncClient, admin_token: str, test_user):
    user_id, _, _ = test_user
    resp = await client.put(
        f"/api/v1/admin/users/{user_id}/status",
        json={"status": "suspended"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert "suspended" in resp.json()["message"]


async def test_admin_activate_user(client: AsyncClient, admin_token: str, test_user):
    user_id, _, _ = test_user
    # Suspend first
    await client.put(
        f"/api/v1/admin/users/{user_id}/status",
        json={"status": "suspended"},
        headers=auth_header(admin_token),
    )
    # Activate
    resp = await client.put(
        f"/api/v1/admin/users/{user_id}/status",
        json={"status": "active"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert "active" in resp.json()["message"]


async def test_admin_invalid_user_status(client: AsyncClient, admin_token: str, test_user):
    user_id, _, _ = test_user
    resp = await client.put(
        f"/api/v1/admin/users/{user_id}/status",
        json={"status": "invalid"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 400


async def test_admin_logs(client: AsyncClient, admin_token: str):
    resp = await client.get("/api/v1/admin/logs", headers=auth_header(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert "pagination" in data


async def test_operator_can_list_jobs(client: AsyncClient, operator_token: str):
    resp = await client.get("/api/v1/admin/jobs", headers=auth_header(operator_token))
    assert resp.status_code == 200


async def test_operator_cannot_access_logs(client: AsyncClient, operator_token: str):
    resp = await client.get("/api/v1/admin/logs", headers=auth_header(operator_token))
    assert resp.status_code == 403


async def test_operator_cannot_suspend_user(client: AsyncClient, operator_token: str, test_user):
    user_id, _, _ = test_user
    resp = await client.put(
        f"/api/v1/admin/users/{user_id}/status",
        json={"status": "suspended"},
        headers=auth_header(operator_token),
    )
    assert resp.status_code == 403


# --- User not found ---

async def test_admin_get_nonexistent_user(client: AsyncClient, admin_token: str):
    fake_id = uuid.uuid4()
    resp = await client.get(f"/api/v1/admin/users/{fake_id}", headers=auth_header(admin_token))
    assert resp.status_code == 404


async def test_admin_suspend_nonexistent_user(client: AsyncClient, admin_token: str):
    fake_id = uuid.uuid4()
    resp = await client.put(
        f"/api/v1/admin/users/{fake_id}/status",
        json={"status": "suspended"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 404


# --- Status filter for user listing ---

async def test_admin_list_users_status_filter(client: AsyncClient, admin_token: str, test_user):
    resp = await client.get("/api/v1/admin/users?status=active", headers=auth_header(admin_token))
    assert resp.status_code == 200
    for user in resp.json()["data"]:
        assert user["status"] == "active"
