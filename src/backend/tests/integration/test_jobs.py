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


async def test_get_job_by_slug(client: AsyncClient, active_job):
    slug = active_job["slug"]
    resp = await client.get(f"/api/v1/jobs/{slug}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["slug"] == slug
    assert data["job_title"] == active_job["job_title"]


async def test_get_job_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/jobs/nonexistent-slug-that-does-not-exist")
    assert resp.status_code == 404


async def test_list_jobs_fts_search(client: AsyncClient, active_job):
    resp = await client.get(f"/api/v1/jobs?q={active_job['organization']}")
    assert resp.status_code == 200


# --- Admin Job CRUD ---


async def test_admin_create_job(client: AsyncClient, admin_token: str):
    uid = uuid.uuid4().hex[:6]
    resp = await client.post(
        "/api/v1/admin/jobs",
        json={
            "job_title": f"Admin Created Job {uid}",
            "slug": f"admin-created-job-{uid}",
            "organization": "Admin Test Org",
            "description": "Admin test job.",
            "status": "active",
        },
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "active"
    assert data["slug"] == f"admin-created-job-{uid}"


async def test_admin_list_all_jobs(client: AsyncClient, admin_token: str, active_job):
    resp = await client.get("/api/v1/admin/jobs", headers=auth_header(admin_token))
    assert resp.status_code == 200
    assert resp.json()["pagination"]["total"] >= 1


async def test_admin_list_jobs_by_status(
    client: AsyncClient, admin_token: str, active_job
):
    resp = await client.get(
        "/api/v1/admin/jobs?status=active", headers=auth_header(admin_token)
    )
    assert resp.status_code == 200
    for job in resp.json()["data"]:
        assert job["status"] == "active"


async def test_admin_update_job(client: AsyncClient, admin_token: str, active_job):
    job_id = active_job["id"]
    resp = await client.put(
        f"/api/v1/admin/jobs/{job_id}",
        json={"total_vacancies": 500},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_vacancies"] == 500


async def test_admin_delete_job(client: AsyncClient, admin_token: str, active_job):
    job_id = active_job["id"]
    resp = await client.delete(
        f"/api/v1/admin/jobs/{job_id}",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 204


async def test_operator_cannot_delete_job(
    client: AsyncClient, operator_token: str, active_job
):
    job_id = active_job["id"]
    resp = await client.delete(
        f"/api/v1/admin/jobs/{job_id}",
        headers=auth_header(operator_token),
    )
    assert resp.status_code == 403


async def test_slug_uniqueness(client: AsyncClient, admin_token: str):
    uid = uuid.uuid4().hex[:4]
    slug = f"unique-slug-test-{uid}"
    resp1 = await client.post(
        "/api/v1/admin/jobs",
        json={
            "job_title": f"Unique Slug Test {uid}",
            "slug": slug,
            "organization": "Test",
            "status": "active",
        },
        headers=auth_header(admin_token),
    )
    resp2 = await client.post(
        "/api/v1/admin/jobs",
        json={
            "job_title": f"Unique Slug Test {uid} copy",
            "slug": slug,
            "organization": "Test",
            "status": "active",
        },
        headers=auth_header(admin_token),
    )
    assert resp1.status_code == 201
    assert resp2.status_code == 409


async def test_unauthenticated_admin_access(client: AsyncClient):
    resp = await client.get("/api/v1/admin/jobs")
    assert resp.status_code in (401, 403)
