"""Integration tests for content endpoints — admit cards, answer keys, results (public + admin CRUD)."""

import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Helpers ────────────────────────────────────────────────────────────────────


async def _create_admit_card(client, admin_token, active_job):
    uid = uuid.uuid4().hex[:4]
    resp = await client.post(
        "/api/v1/admin/admit-cards",
        json={
            "slug": f"admit-card-{uid}",
            "title": f"AC {uid}",
            "job_id": active_job["id"],
            "download_url": "https://example.com/admit.pdf",
        },
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201
    return resp.json()


async def _create_answer_key(client, admin_token, active_job):
    uid = uuid.uuid4().hex[:4]
    resp = await client.post(
        "/api/v1/admin/answer-keys",
        json={
            "slug": f"answer-key-{uid}",
            "title": f"AK {uid}",
            "job_id": active_job["id"],
        },
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201
    return resp.json()


async def _create_result(client, admin_token, active_job):
    uid = uuid.uuid4().hex[:4]
    resp = await client.post(
        "/api/v1/admin/results",
        json={
            "slug": f"result-{uid}",
            "title": f"Res {uid}",
            "job_id": active_job["id"],
            "result_type": "final",
        },
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201
    return resp.json()


# ══════════════════════════════════════════════════════════════════
# ADMIT CARDS
# ══════════════════════════════════════════════════════════════════


async def test_list_admit_cards(client: AsyncClient, admin_token: str, active_job):
    await _create_admit_card(client, admin_token, active_job)
    resp = await client.get("/api/v1/admit-cards")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert "pagination" in data
    assert data["pagination"]["total"] >= 1


async def test_list_admit_cards_pagination(
    client: AsyncClient, admin_token: str, active_job
):
    await _create_admit_card(client, admin_token, active_job)
    resp = await client.get("/api/v1/admit-cards?limit=1&offset=0")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) <= 1


async def test_get_admit_card_by_slug(
    client: AsyncClient, admin_token: str, active_job
):
    card = await _create_admit_card(client, admin_token, active_job)
    resp = await client.get(f"/api/v1/admit-cards/{card['slug']}")
    assert resp.status_code == 200
    assert resp.json()["slug"] == card["slug"]


async def test_get_admit_card_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/admit-cards/nonexistent-slug")
    assert resp.status_code == 404


async def test_admin_create_admit_card(
    client: AsyncClient, admin_token: str, active_job
):
    resp = await client.post(
        "/api/v1/admin/admit-cards",
        json={
            "slug": "ssc-cgl-admit-card",
            "title": "SSC CGL Admit Card",
            "job_id": active_job["id"],
            "download_url": "https://example.com/admit.pdf",
        },
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201
    assert resp.json()["title"] == "SSC CGL Admit Card"


async def test_admin_create_admit_card_no_parent_fails(
    client: AsyncClient, admin_token: str
):
    resp = await client.post(
        "/api/v1/admin/admit-cards",
        json={
            "title": "No Parent",
            "slug": "no-parent",
            "download_url": "https://example.com/admit.pdf",
        },
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 400


async def test_admin_create_admit_card_both_parents_fails(
    client: AsyncClient, admin_token: str, active_job, active_admission
):
    resp = await client.post(
        "/api/v1/admin/admit-cards",
        json={
            "title": "Both Parents",
            "slug": "both-parents",
            "job_id": active_job["id"],
            "admission_id": active_admission["id"],
            "download_url": "https://example.com/admit.pdf",
        },
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 400


async def test_admin_list_admit_cards(
    client: AsyncClient, admin_token: str, active_job
):
    await _create_admit_card(client, admin_token, active_job)
    resp = await client.get(
        "/api/v1/admin/admit-cards", headers=auth_header(admin_token)
    )
    assert resp.status_code == 200
    assert resp.json()["pagination"]["total"] >= 1


async def test_admin_update_admit_card(
    client: AsyncClient, admin_token: str, active_job
):
    card = await _create_admit_card(client, admin_token, active_job)
    resp = await client.put(
        f"/api/v1/admin/admit-cards/{card['id']}",
        json={"title": "Updated Admit Card"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Admit Card"


async def test_admin_update_admit_card_not_found(client: AsyncClient, admin_token: str):
    resp = await client.put(
        f"/api/v1/admin/admit-cards/{uuid.uuid4()}",
        json={"title": "X"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 404


async def test_admin_delete_admit_card(
    client: AsyncClient, admin_token: str, active_job
):
    card = await _create_admit_card(client, admin_token, active_job)
    resp = await client.delete(
        f"/api/v1/admin/admit-cards/{card['id']}",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 204


async def test_admin_delete_admit_card_not_found(client: AsyncClient, admin_token: str):
    resp = await client.delete(
        f"/api/v1/admin/admit-cards/{uuid.uuid4()}",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 404


async def test_admit_cards_admin_requires_auth(client: AsyncClient, active_job):
    resp = await client.post(
        "/api/v1/admin/admit-cards", json={"title": "X", "job_id": active_job["id"]}
    )
    assert resp.status_code in (401, 403)


# ══════════════════════════════════════════════════════════════════
# ANSWER KEYS
# ══════════════════════════════════════════════════════════════════


async def test_list_answer_keys(client: AsyncClient, admin_token: str, active_job):
    await _create_answer_key(client, admin_token, active_job)
    resp = await client.get("/api/v1/answer-keys")
    assert resp.status_code == 200
    assert resp.json()["pagination"]["total"] >= 1


async def test_get_answer_key_by_slug(
    client: AsyncClient, admin_token: str, active_job
):
    key = await _create_answer_key(client, admin_token, active_job)
    resp = await client.get(f"/api/v1/answer-keys/{key['slug']}")
    assert resp.status_code == 200
    assert resp.json()["slug"] == key["slug"]


async def test_get_answer_key_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/answer-keys/nonexistent-slug")
    assert resp.status_code == 404


async def test_admin_create_answer_key(
    client: AsyncClient, admin_token: str, active_job
):
    resp = await client.post(
        "/api/v1/admin/answer-keys",
        json={
            "slug": "ssc-cgl-answer-key",
            "title": "SSC CGL Answer Key",
            "job_id": active_job["id"],
        },
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201
    assert "id" in resp.json()


async def test_admin_update_answer_key(
    client: AsyncClient, admin_token: str, active_job
):
    key = await _create_answer_key(client, admin_token, active_job)
    resp = await client.put(
        f"/api/v1/admin/answer-keys/{key['id']}",
        json={"title": "Updated Answer Key"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Answer Key"


async def test_admin_update_answer_key_not_found(client: AsyncClient, admin_token: str):
    resp = await client.put(
        f"/api/v1/admin/answer-keys/{uuid.uuid4()}",
        json={"title": "X"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 404


async def test_admin_delete_answer_key(
    client: AsyncClient, admin_token: str, active_job
):
    key = await _create_answer_key(client, admin_token, active_job)
    resp = await client.delete(
        f"/api/v1/admin/answer-keys/{key['id']}",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 204


async def test_admin_delete_answer_key_not_found(client: AsyncClient, admin_token: str):
    resp = await client.delete(
        f"/api/v1/admin/answer-keys/{uuid.uuid4()}",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 404


# ══════════════════════════════════════════════════════════════════
# RESULTS
# ══════════════════════════════════════════════════════════════════


async def test_list_results(client: AsyncClient, admin_token: str, active_job):
    await _create_result(client, admin_token, active_job)
    resp = await client.get("/api/v1/results")
    assert resp.status_code == 200
    assert resp.json()["pagination"]["total"] >= 1


async def test_get_result_by_slug(client: AsyncClient, admin_token: str, active_job):
    result = await _create_result(client, admin_token, active_job)
    resp = await client.get(f"/api/v1/results/{result['slug']}")
    assert resp.status_code == 200
    assert resp.json()["slug"] == result["slug"]


async def test_get_result_not_found(client: AsyncClient):
    resp = await client.get("/api/v1/results/nonexistent-slug")
    assert resp.status_code == 404


async def test_admin_create_result(client: AsyncClient, admin_token: str, active_job):
    resp = await client.post(
        "/api/v1/admin/results",
        json={
            "slug": "ssc-cgl-result",
            "title": "SSC CGL Result",
            "job_id": active_job["id"],
            "result_type": "final",
        },
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 201
    assert "id" in resp.json()


async def test_admin_update_result(client: AsyncClient, admin_token: str, active_job):
    result = await _create_result(client, admin_token, active_job)
    resp = await client.put(
        f"/api/v1/admin/results/{result['id']}",
        json={"title": "Updated Result"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "Updated Result"


async def test_admin_update_result_not_found(client: AsyncClient, admin_token: str):
    resp = await client.put(
        f"/api/v1/admin/results/{uuid.uuid4()}",
        json={"title": "X"},
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 404


async def test_admin_delete_result(client: AsyncClient, admin_token: str, active_job):
    result = await _create_result(client, admin_token, active_job)
    resp = await client.delete(
        f"/api/v1/admin/results/{result['id']}",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 204


async def test_admin_delete_result_not_found(client: AsyncClient, admin_token: str):
    resp = await client.delete(
        f"/api/v1/admin/results/{uuid.uuid4()}",
        headers=auth_header(admin_token),
    )
    assert resp.status_code == 404


async def test_results_admin_requires_auth(client: AsyncClient, active_job):
    resp = await client.post(
        "/api/v1/admin/results",
        json={"title": "X", "job_id": active_job["id"], "result_type": "final"},
    )
    assert resp.status_code in (401, 403)
