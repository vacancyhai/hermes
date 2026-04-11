"""Integration tests for watch endpoints — watch/unwatch jobs & exams, list watched."""

import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Job watch ──────────────────────────────────────────────────────────────────


async def test_watch_job(client: AsyncClient, user_token: str, active_job):
    job_id = active_job["id"]
    resp = await client.post(
        f"/api/v1/jobs/{job_id}/watch", headers=auth_header(user_token)
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["watching"] is True


async def test_watch_job_idempotent(client: AsyncClient, user_token: str, active_job):
    job_id = active_job["id"]
    await client.post(f"/api/v1/jobs/{job_id}/watch", headers=auth_header(user_token))
    resp = await client.post(
        f"/api/v1/jobs/{job_id}/watch", headers=auth_header(user_token)
    )
    assert resp.status_code == 200
    assert "already" in resp.json()["message"].lower()


async def test_watch_job_not_found(client: AsyncClient, user_token: str):
    fake_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/jobs/{fake_id}/watch", headers=auth_header(user_token)
    )
    assert resp.status_code == 404


async def test_watch_job_requires_auth(client: AsyncClient, active_job):
    job_id = active_job["id"]
    resp = await client.post(f"/api/v1/jobs/{job_id}/watch")
    assert resp.status_code in (401, 403)


async def test_unwatch_job(client: AsyncClient, user_token: str, active_job):
    job_id = active_job["id"]
    await client.post(f"/api/v1/jobs/{job_id}/watch", headers=auth_header(user_token))
    resp = await client.delete(
        f"/api/v1/jobs/{job_id}/watch", headers=auth_header(user_token)
    )
    assert resp.status_code == 200
    assert resp.json()["watching"] is False


async def test_unwatch_job_not_watching(
    client: AsyncClient, user_token: str, active_job
):
    job_id = active_job["id"]
    resp = await client.delete(
        f"/api/v1/jobs/{job_id}/watch", headers=auth_header(user_token)
    )
    assert resp.status_code == 404


async def test_unwatch_job_requires_auth(client: AsyncClient, active_job):
    job_id = active_job["id"]
    resp = await client.delete(f"/api/v1/jobs/{job_id}/watch")
    assert resp.status_code in (401, 403)


# ── Admission watch ──────────────────────────────────────────────────────────────


async def test_watch_exam(client: AsyncClient, user_token: str, active_exam):
    admission_id = active_exam["id"]
    resp = await client.post(
        f"/api/v1/admissions/{admission_id}/watch", headers=auth_header(user_token)
    )
    assert resp.status_code == 200
    assert resp.json()["watching"] is True


async def test_watch_exam_idempotent(client: AsyncClient, user_token: str, active_exam):
    admission_id = active_exam["id"]
    await client.post(
        f"/api/v1/admissions/{admission_id}/watch", headers=auth_header(user_token)
    )
    resp = await client.post(
        f"/api/v1/admissions/{admission_id}/watch", headers=auth_header(user_token)
    )
    assert resp.status_code == 200
    assert "already" in resp.json()["message"].lower()


async def test_watch_exam_not_found(client: AsyncClient, user_token: str):
    fake_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/admissions/{fake_id}/watch", headers=auth_header(user_token)
    )
    assert resp.status_code == 404


async def test_unwatch_exam(client: AsyncClient, user_token: str, active_exam):
    admission_id = active_exam["id"]
    await client.post(
        f"/api/v1/admissions/{admission_id}/watch", headers=auth_header(user_token)
    )
    resp = await client.delete(
        f"/api/v1/admissions/{admission_id}/watch", headers=auth_header(user_token)
    )
    assert resp.status_code == 200
    assert resp.json()["watching"] is False


async def test_unwatch_exam_not_watching(
    client: AsyncClient, user_token: str, active_exam
):
    admission_id = active_exam["id"]
    resp = await client.delete(
        f"/api/v1/admissions/{admission_id}/watch", headers=auth_header(user_token)
    )
    assert resp.status_code == 404


# ── List watched ───────────────────────────────────────────────────────────────


async def test_list_watched_empty(client: AsyncClient, user_token: str):
    resp = await client.get("/api/v1/users/me/watched", headers=auth_header(user_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "jobs" in data
    assert "exams" in data
    assert "total" in data


async def test_list_watched_includes_job(
    client: AsyncClient, user_token: str, active_job
):
    job_id = active_job["id"]
    await client.post(f"/api/v1/jobs/{job_id}/watch", headers=auth_header(user_token))
    resp = await client.get("/api/v1/users/me/watched", headers=auth_header(user_token))
    assert resp.status_code == 200
    watched_ids = [j["id"] for j in resp.json()["jobs"]]
    assert job_id in watched_ids


async def test_list_watched_includes_exam(
    client: AsyncClient, user_token: str, active_exam
):
    admission_id = active_exam["id"]
    await client.post(
        f"/api/v1/admissions/{admission_id}/watch", headers=auth_header(user_token)
    )
    resp = await client.get("/api/v1/users/me/watched", headers=auth_header(user_token))
    assert resp.status_code == 200
    watched_ids = [e["id"] for e in resp.json()["exams"]]
    assert admission_id in watched_ids


async def test_list_watched_after_unwatch(
    client: AsyncClient, user_token: str, active_job
):
    job_id = active_job["id"]
    await client.post(f"/api/v1/jobs/{job_id}/watch", headers=auth_header(user_token))
    await client.delete(f"/api/v1/jobs/{job_id}/watch", headers=auth_header(user_token))
    resp = await client.get("/api/v1/users/me/watched", headers=auth_header(user_token))
    assert resp.status_code == 200
    watched_ids = [j["id"] for j in resp.json()["jobs"]]
    assert job_id not in watched_ids


async def test_list_watched_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/users/me/watched")
    assert resp.status_code in (401, 403)
