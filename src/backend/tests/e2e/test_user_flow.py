"""Integration tests — end-to-end flows spanning multiple endpoints."""

import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}

pytestmark = pytest.mark.asyncio


async def test_full_user_flow(client: AsyncClient):
    """Firebase sign-in → view jobs → track application → update status → delete."""
    email = f"flow_{uuid.uuid4().hex[:8]}@test.com"
    firebase_uid = f"flow-uid-{uuid.uuid4().hex[:12]}"

    # Sign in via Firebase verify-token (creates new user)
    decoded = {
        "uid": firebase_uid,
        "email": email,
        "email_verified": True,
        "name": "Flow User",
        "firebase": {"sign_in_provider": "password"},
    }
    with patch("app.firebase.verify_id_token", return_value=decoded):
        resp = await client.post("/api/v1/auth/verify-token", json={"id_token": "fake-token"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    headers = auth_header(token)

    # View jobs
    resp = await client.get("/api/v1/jobs")
    assert resp.status_code == 200
    jobs = resp.json()["data"]

    if not jobs:
        pytest.skip("No active jobs available for integration test")

    job = jobs[0]

    # Track the job
    resp = await client.post("/api/v1/applications", json={"job_id": job["id"]}, headers=headers)
    assert resp.status_code == 201
    app_id = resp.json()["id"]

    # Update status
    resp = await client.put(
        f"/api/v1/applications/{app_id}",
        json={"status": "exam_completed", "notes": "Exam went well"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "exam_completed"

    # Check stats
    resp = await client.get("/api/v1/applications/stats", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1

    # Delete
    resp = await client.delete(f"/api/v1/applications/{app_id}", headers=headers)
    assert resp.status_code == 204


async def test_admin_job_lifecycle(client: AsyncClient, admin_token: str):
    """Create draft → update → approve → verify published → soft delete."""
    headers = auth_header(admin_token)
    title = f"Lifecycle Test {uuid.uuid4().hex[:6]}"

    # Create draft
    resp = await client.post("/api/v1/admin/jobs", json={
        "job_title": title,
        "organization": "Lifecycle Org",
        "job_type": "latest_job",
        "qualification_level": "graduate",
        "total_vacancies": 50,
        "description": "Integration test job.",
        "status": "draft",
    }, headers=headers)
    assert resp.status_code == 201
    job_id = resp.json()["id"]

    # Draft should NOT appear in public listing (default active)
    resp = await client.get("/api/v1/jobs")
    job_ids = [j["id"] for j in resp.json()["data"]]
    assert job_id not in job_ids

    # Update draft
    resp = await client.put(f"/api/v1/admin/jobs/{job_id}", json={
        "total_vacancies": 75,
        "fee_general": 500,
        "fee_sc_st": 0,
    }, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total_vacancies"] == 75

    # Approve
    resp = await client.put(f"/api/v1/admin/jobs/{job_id}/approve", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"
    assert resp.json()["published_at"] is not None

    # Now visible in public listing
    resp = await client.get(f"/api/v1/jobs/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["total_vacancies"] == 75

    # Soft delete
    resp = await client.delete(f"/api/v1/admin/jobs/{job_id}", headers=headers)
    assert resp.status_code == 204

    # ID still resolves but status is cancelled
    resp = await client.get(f"/api/v1/jobs/{job_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


async def test_admin_user_management_flow(client: AsyncClient, admin_token: str):
    """Create user via Firebase → suspend → verify suspended → activate → verify active."""
    admin_headers = auth_header(admin_token)

    # Create a user via Firebase verify-token
    email = f"mgmt_{uuid.uuid4().hex[:8]}@test.com"
    firebase_uid = f"mgmt-uid-{uuid.uuid4().hex[:12]}"
    decoded = {
        "uid": firebase_uid,
        "email": email,
        "email_verified": True,
        "name": "Managed User",
        "firebase": {"sign_in_provider": "password"},
    }
    with patch("app.firebase.verify_id_token", return_value=decoded):
        resp = await client.post("/api/v1/auth/verify-token", json={"id_token": "fake-token"})
    assert resp.status_code == 200
    user_token_first = resp.json()["access_token"]
    # Extract user_id from JWT
    from jose import jwt
    from app.config import settings
    user_id = jwt.decode(user_token_first, settings.JWT_SECRET_KEY, algorithms=["HS256"])["sub"]

    # Admin suspends user
    resp = await client.put(
        f"/api/v1/admin/users/{user_id}/status",
        json={"status": "suspended"},
        headers=admin_headers,
    )
    assert resp.status_code == 200

    # Suspended user can't verify-token
    with patch("app.firebase.verify_id_token", return_value=decoded):
        resp = await client.post("/api/v1/auth/verify-token", json={"id_token": "fake-token"})
    assert resp.status_code == 403

    # Admin activates user
    resp = await client.put(
        f"/api/v1/admin/users/{user_id}/status",
        json={"status": "active"},
        headers=admin_headers,
    )
    assert resp.status_code == 200

    # Active user can verify-token again
    with patch("app.firebase.verify_id_token", return_value=decoded):
        resp = await client.post("/api/v1/auth/verify-token", json={"id_token": "fake-token"})
    assert resp.status_code == 200


async def test_rbac_admin_vs_operator(client: AsyncClient, admin_token: str, operator_token: str, test_user):
    """Verify role-based access: operator can list, but only admin can delete/suspend."""
    user_id, _, _ = test_user

    # Operator can list jobs
    resp = await client.get("/api/v1/admin/jobs", headers=auth_header(operator_token))
    assert resp.status_code == 200

    # Operator can create job
    resp = await client.post("/api/v1/admin/jobs", json={
        "job_title": "Operator Job",
        "organization": "Operator Org",
        "job_type": "latest_job",
        "description": "op test",
        "status": "draft",
    }, headers=auth_header(operator_token))
    assert resp.status_code == 201
    job_id = resp.json()["id"]

    # Operator CANNOT delete job (admin only)
    resp = await client.delete(f"/api/v1/admin/jobs/{job_id}", headers=auth_header(operator_token))
    assert resp.status_code == 403

    # Operator CANNOT suspend user (admin only)
    resp = await client.put(
        f"/api/v1/admin/users/{user_id}/status",
        json={"status": "suspended"},
        headers=auth_header(operator_token),
    )
    assert resp.status_code == 403

    # Operator CANNOT view logs (admin only)
    resp = await client.get("/api/v1/admin/logs", headers=auth_header(operator_token))
    assert resp.status_code == 403

    # Admin CAN delete
    resp = await client.delete(f"/api/v1/admin/jobs/{job_id}", headers=auth_header(admin_token))
    assert resp.status_code == 204
