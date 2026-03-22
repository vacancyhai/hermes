"""Tests for application tracking endpoints."""

import uuid

import pytest
from httpx import AsyncClient


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}

pytestmark = pytest.mark.asyncio


async def test_track_job(client: AsyncClient, user_token: str, active_job):
    resp = await client.post(
        "/api/v1/applications",
        json={"job_id": active_job["id"], "notes": "Test application"},
        headers=auth_header(user_token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "applied"
    assert data["job"]["job_title"] == active_job["job_title"]


async def test_track_duplicate_fails(client: AsyncClient, user_token: str, active_job):
    await client.post(
        "/api/v1/applications",
        json={"job_id": active_job["id"]},
        headers=auth_header(user_token),
    )
    resp = await client.post(
        "/api/v1/applications",
        json={"job_id": active_job["id"]},
        headers=auth_header(user_token),
    )
    assert resp.status_code == 409


async def test_track_nonexistent_job(client: AsyncClient, user_token: str):
    fake_id = str(uuid.uuid4())
    resp = await client.post(
        "/api/v1/applications",
        json={"job_id": fake_id},
        headers=auth_header(user_token),
    )
    assert resp.status_code == 404


async def test_list_applications(client: AsyncClient, user_token: str, active_job):
    await client.post(
        "/api/v1/applications",
        json={"job_id": active_job["id"]},
        headers=auth_header(user_token),
    )
    resp = await client.get("/api/v1/applications", headers=auth_header(user_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert data["pagination"]["total"] >= 1


async def test_application_stats(client: AsyncClient, user_token: str, active_job):
    await client.post(
        "/api/v1/applications",
        json={"job_id": active_job["id"]},
        headers=auth_header(user_token),
    )
    resp = await client.get("/api/v1/applications/stats", headers=auth_header(user_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "total" in data
    assert data["total"] >= 1


async def test_update_application_status(client: AsyncClient, user_token: str, active_job):
    create_resp = await client.post(
        "/api/v1/applications",
        json={"job_id": active_job["id"]},
        headers=auth_header(user_token),
    )
    app_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/v1/applications/{app_id}",
        json={"status": "admit_card_released", "is_priority": True},
        headers=auth_header(user_token),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "admit_card_released"
    assert resp.json()["is_priority"] is True


async def test_update_application_invalid_status(client: AsyncClient, user_token: str, active_job):
    create_resp = await client.post(
        "/api/v1/applications",
        json={"job_id": active_job["id"]},
        headers=auth_header(user_token),
    )
    app_id = create_resp.json()["id"]

    resp = await client.put(
        f"/api/v1/applications/{app_id}",
        json={"status": "invalid_status"},
        headers=auth_header(user_token),
    )
    assert resp.status_code == 400


async def test_delete_application(client: AsyncClient, user_token: str, active_job):
    create_resp = await client.post(
        "/api/v1/applications",
        json={"job_id": active_job["id"]},
        headers=auth_header(user_token),
    )
    app_id = create_resp.json()["id"]

    resp = await client.delete(
        f"/api/v1/applications/{app_id}",
        headers=auth_header(user_token),
    )
    assert resp.status_code == 204

    # Verify gone
    resp = await client.get(
        f"/api/v1/applications/{app_id}",
        headers=auth_header(user_token),
    )
    assert resp.status_code == 404


async def test_application_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/applications")
    assert resp.status_code in (401, 403)


async def test_get_single_application(client: AsyncClient, user_token: str, active_job):
    create_resp = await client.post(
        "/api/v1/applications",
        json={"job_id": active_job["id"], "notes": "Detail test"},
        headers=auth_header(user_token),
    )
    app_id = create_resp.json()["id"]

    resp = await client.get(
        f"/api/v1/applications/{app_id}",
        headers=auth_header(user_token),
    )
    assert resp.status_code == 200
    assert resp.json()["notes"] == "Detail test"
