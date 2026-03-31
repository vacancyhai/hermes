"""Tests for job vacancy endpoints (public + admin CRUD)."""

import uuid

import pytest
from httpx import AsyncClient


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}

pytestmark = pytest.mark.asyncio


# --- Public Job Listing ---

async def test_list_jobs_default_active(client: AsyncClient, active_job):
    resp = await client.get("/api/v1/jobs")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert "pagination" in data
    assert data["pagination"]["total"] >= 1


async def test_list_jobs_pagination(client: AsyncClient, active_job):
    resp = await client.get("/api/v1/jobs?limit=1&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) <= 1
    assert "has_more" in data["pagination"]


async def test_list_jobs_filter_by_org(client: AsyncClient, active_job):
    resp = await client.get(f"/api/v1/jobs?organization={active_job['organization']}")
    assert resp.status_code == 200
    assert resp.json()["pagination"]["total"] >= 1


async def test_get_job_by_id(client: AsyncClient, active_job):
    job_id = active_job["id"]
    resp = await client.get(f"/api/v1/jobs/{job_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == job_id
    assert data["job_title"] == active_job["job_title"]


async def test_get_job_increments_views(client: AsyncClient, active_job):
    job_id = active_job["id"]
    initial = active_job["views"]
    await client.get(f"/api/v1/jobs/{job_id}")
    resp = await client.get(f"/api/v1/jobs/{job_id}")
    assert resp.json()["views"] >= initial + 1


async def test_get_job_not_found(client: AsyncClient):
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/jobs/{fake_id}")
    assert resp.status_code == 404


async def test_list_jobs_fts_search(client: AsyncClient, active_job):
    resp = await client.get(f"/api/v1/jobs?q={active_job['organization']}")
    assert resp.status_code == 200


# --- Admin Job CRUD ---

async def test_admin_create_job(client: AsyncClient, admin_token: str):
    resp = await client.post(
        "/api/v1/admin/jobs",
        json={
            "job_title": f"Admin Created Job {uuid.uuid4().hex[:6]}",
            "organization": "Admin Test Org",
            "description": "Admin test job.",
            "status": "draft",
        },
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "draft"
    assert "slug" in data


async def test_admin_list_all_jobs(client: AsyncClient, admin_token: str, active_job):
    resp = await client.get("/api/v1/admin/jobs", headers=auth_header(admin_token))
    assert resp.status_code == 200
    assert resp.json()["pagination"]["total"] >= 1


async def test_admin_list_jobs_by_status(client: AsyncClient, admin_token: str, draft_job):
    resp = await client.get("/api/v1/admin/jobs?status=draft", headers=auth_header(admin_token))
    assert resp.status_code == 200
    for job in resp.json()["data"]:
        assert job["status"] == "draft"


async def test_admin_update_job(client: AsyncClient, admin_token: str, draft_job):
    job_id = draft_job["id"]
    resp = await client.put(
        f"/api/v1/admin/jobs/{job_id}",
        json={"total_vacancies": 500, "is_featured": True},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_vacancies"] == 500
    assert data["is_featured"] is True


async def test_admin_approve_draft(client: AsyncClient, admin_token: str, draft_job):
    job_id = draft_job["id"]
    resp = await client.put(
        f"/api/v1/admin/jobs/{job_id}/approve",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "active"
    assert data["published_at"] is not None


async def test_admin_approve_non_draft_fails(client: AsyncClient, admin_token: str, active_job):
    job_id = active_job["id"]
    resp = await client.put(
        f"/api/v1/admin/jobs/{job_id}/approve",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 400


async def test_admin_delete_job(client: AsyncClient, admin_token: str, draft_job):
    job_id = draft_job["id"]
    resp = await client.delete(
        f"/api/v1/admin/jobs/{job_id}",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 204


async def test_operator_cannot_delete_job(client: AsyncClient, operator_token: str, active_job):
    job_id = active_job["id"]
    resp = await client.delete(
        f"/api/v1/admin/jobs/{job_id}",
        headers=auth_header(operator_token),
    )
    assert resp.status_code == 403


async def test_slug_uniqueness(client: AsyncClient, admin_token: str):
    title = f"Unique Slug Test {uuid.uuid4().hex[:4]}"
    resp1 = await client.post(
        "/api/v1/admin/jobs",
        json={"job_title": title, "organization": "Test", "description": "d", "status": "draft"},
        headers=auth_header(admin_token),
    )
    resp2 = await client.post(
        "/api/v1/admin/jobs",
        json={"job_title": title, "organization": "Test", "description": "d", "status": "draft"},
        headers=auth_header(admin_token),
    )
    assert resp1.status_code == 201
    assert resp2.status_code == 201
    assert resp1.json()["slug"] != resp2.json()["slug"]


async def test_unauthenticated_admin_access(client: AsyncClient):
    resp = await client.get("/api/v1/admin/jobs")
    assert resp.status_code in (401, 403)
