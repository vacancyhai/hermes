"""Integration tests for entrance exam endpoints — public list/detail + admin CRUD."""

import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Public: list ───────────────────────────────────────────────────────────────


async def test_list_exams(client: AsyncClient, active_exam):
    resp = await client.get("/api/v1/entrance-exams")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert "pagination" in data
    assert data["pagination"]["total"] >= 1


async def test_list_exams_pagination(client: AsyncClient, active_exam):
    resp = await client.get("/api/v1/entrance-exams?limit=1&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) <= 1
    assert "has_more" in data["pagination"]


async def test_list_exams_filter_by_stream(client: AsyncClient, active_exam):
    stream = active_exam["stream"]
    resp = await client.get(f"/api/v1/entrance-exams?stream={stream}")
    assert resp.status_code == 200
    for item in resp.json()["data"]:
        assert item["stream"] == stream


async def test_list_exams_fts_search(client: AsyncClient, active_exam):
    resp = await client.get(
        f"/api/v1/entrance-exams?q={active_exam['conducting_body']}"
    )
    assert resp.status_code == 200


# ── Public: detail ─────────────────────────────────────────────────────────────


async def test_get_exam_by_id(client: AsyncClient, active_exam):
    exam_id = active_exam["id"]
    resp = await client.get(f"/api/v1/entrance-exams/{exam_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == exam_id
    assert "admit_cards" in data
    assert "answer_keys" in data
    assert "results" in data


async def test_get_exam_not_found(client: AsyncClient):
    fake_id = uuid.uuid4()
    resp = await client.get(f"/api/v1/entrance-exams/{fake_id}")
    assert resp.status_code == 404


# ── Admin: list ────────────────────────────────────────────────────────────────


async def test_admin_list_exams(client: AsyncClient, admin_token: str, active_exam):
    resp = await client.get(
        "/api/v1/admin/entrance-exams", headers=auth_header(admin_token)
    )
    assert resp.status_code == 200
    assert resp.json()["pagination"]["total"] >= 1


async def test_admin_list_exams_filter_by_status(
    client: AsyncClient, admin_token: str, active_exam
):
    resp = await client.get(
        "/api/v1/admin/entrance-exams?status=active", headers=auth_header(admin_token)
    )
    assert resp.status_code == 200
    for item in resp.json()["data"]:
        assert item["status"] == "active"


async def test_admin_list_exams_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/v1/admin/entrance-exams")
    assert resp.status_code in (401, 403)


# ── Admin: create ──────────────────────────────────────────────────────────────


async def test_admin_create_exam(client: AsyncClient, admin_token: str):
    resp = await client.post(
        "/api/v1/admin/entrance-exams",
        json={
            "exam_name": f"JEE Main {uuid.uuid4().hex[:4]}",
            "conducting_body": "NTA",
            "stream": "engineering",
            "status": "upcoming",
        },
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert "slug" in data
    assert data["stream"] == "engineering"


async def test_admin_create_exam_slug_unique(client: AsyncClient, admin_token: str):
    name = f"Slug Exam {uuid.uuid4().hex[:4]}"
    resp1 = await client.post(
        "/api/v1/admin/entrance-exams",
        json={"exam_name": name, "conducting_body": "NTA", "status": "upcoming"},
        headers=auth_header(admin_token),
    )
    resp2 = await client.post(
        "/api/v1/admin/entrance-exams",
        json={"exam_name": name, "conducting_body": "NTA", "status": "upcoming"},
        headers=auth_header(admin_token),
    )
    assert resp1.status_code == 201
    assert resp2.status_code == 201
    assert resp1.json()["slug"] != resp2.json()["slug"]


async def test_operator_can_create_exam(client: AsyncClient, operator_token: str):
    resp = await client.post(
        "/api/v1/admin/entrance-exams",
        json={
            "exam_name": f"Operator Exam {uuid.uuid4().hex[:4]}",
            "conducting_body": "NTA",
            "status": "upcoming",
        },
        headers=auth_header(operator_token),
    )
    assert resp.status_code == 201


# ── Admin: update ──────────────────────────────────────────────────────────────


async def test_admin_update_exam(client: AsyncClient, admin_token: str, active_exam):
    exam_id = active_exam["id"]
    resp = await client.put(
        f"/api/v1/admin/entrance-exams/{exam_id}",
        json={"status": "completed"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


async def test_admin_update_exam_not_found(client: AsyncClient, admin_token: str):
    fake_id = uuid.uuid4()
    resp = await client.put(
        f"/api/v1/admin/entrance-exams/{fake_id}",
        json={"status": "completed"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 404


# ── Admin: delete ──────────────────────────────────────────────────────────────


async def test_admin_delete_exam(client: AsyncClient, admin_token: str):
    create_resp = await client.post(
        "/api/v1/admin/entrance-exams",
        json={
            "exam_name": f"Delete Me {uuid.uuid4().hex[:4]}",
            "conducting_body": "NTA",
            "status": "upcoming",
        },
        headers=auth_header(admin_token),
    )
    assert create_resp.status_code == 201
    exam_id = create_resp.json()["id"]

    resp = await client.delete(
        f"/api/v1/admin/entrance-exams/{exam_id}",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 204


async def test_admin_delete_exam_not_found(client: AsyncClient, admin_token: str):
    fake_id = uuid.uuid4()
    resp = await client.delete(
        f"/api/v1/admin/entrance-exams/{fake_id}",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 404
