"""Cross-service E2E tests — Frontend → Backend → DB.

Flows covered:
  1. Admin job lifecycle: create draft → approve → visible on user frontend → delete
  2. Admin frontend login: CSRF-aware login → protected pages → logout
"""

import re
import uuid

import requests


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


# ── Shared fixture ─────────────────────────────────────────────────────────────


import pytest


@pytest.fixture
def admin_api_token(backend_url, admin_credentials):
    """Obtain a JWT token for the admin user via the backend API."""
    resp = requests.post(
        f"{backend_url}/api/v1/auth/admin/login",
        json=admin_credentials,
        timeout=10,
    )
    assert resp.status_code == 200, f"Admin login failed: {resp.text}"
    return resp.json()["access_token"]


# ── Flow 1: Job lifecycle across services ──────────────────────────────────────


def test_job_lifecycle_visible_on_frontend(backend_url, frontend_url, admin_api_token):
    """Admin creates draft → approves → job visible on user frontend → soft delete."""
    title = f"E2E Job {uuid.uuid4().hex[:8]}"

    # Create draft job
    resp = requests.post(
        f"{backend_url}/api/v1/admin/jobs",
        json={
            "job_title": title,
            "organization": "E2E Test Org",
            "qualification_level": "graduate",
            "total_vacancies": 10,
            "description": "E2E test job — auto-created.",
            "status": "draft",
        },
        headers=_auth(admin_api_token),
        timeout=10,
    )
    assert resp.status_code == 201, f"Job creation failed: {resp.text}"
    job_id = resp.json()["id"]

    # Draft must NOT appear in public listing
    resp = requests.get(f"{backend_url}/api/v1/jobs", timeout=10)
    public_ids = [j["id"] for j in resp.json().get("data", [])]
    assert job_id not in public_ids, "Draft job must not appear in public listing"

    # Approve the job
    resp = requests.put(
        f"{backend_url}/api/v1/admin/jobs/{job_id}/approve",
        headers=_auth(admin_api_token),
        timeout=10,
    )
    assert resp.status_code == 200, f"Approve failed: {resp.text}"
    assert resp.json()["status"] == "active"

    # Approved job must appear in public listing
    resp = requests.get(f"{backend_url}/api/v1/jobs", timeout=10)
    public_ids = [j["id"] for j in resp.json().get("data", [])]
    assert job_id in public_ids, "Approved job must appear in public listing"

    # User frontend /jobs page must render without error
    resp = requests.get(f"{frontend_url}/jobs", timeout=10)
    assert resp.status_code == 200, "User frontend /jobs page returned error"

    # Soft delete
    resp = requests.delete(
        f"{backend_url}/api/v1/admin/jobs/{job_id}",
        headers=_auth(admin_api_token),
        timeout=10,
    )
    assert resp.status_code == 204, f"Delete failed: {resp.text}"

    # After deletion, status is cancelled
    resp = requests.get(f"{backend_url}/api/v1/jobs/{job_id}", timeout=10)
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


# ── Flow 2: Admin frontend login → navigate → logout ──────────────────────────


def test_admin_frontend_login_flow(admin_url, admin_credentials):
    """Admin logs in via admin frontend, navigates protected pages, then logs out."""
    s = requests.Session()

    # GET /login — server sets csrf_token in session and renders it in the form
    get_resp = s.get(f"{admin_url}/login", timeout=10)
    assert get_resp.status_code == 200

    # Extract csrf_token from rendered HTML
    match = re.search(r'name="csrf_token"\s+value="([^"]+)"', get_resp.text)
    assert match, "csrf_token not found in login form HTML"
    csrf_token = match.group(1)

    # POST login with CSRF token
    resp = s.post(
        f"{admin_url}/login",
        data={
            "email": admin_credentials["email"],
            "password": admin_credentials["password"],
            "csrf_token": csrf_token,
        },
        allow_redirects=True,
        timeout=10,
    )
    assert resp.status_code == 200
    assert "/login" not in resp.url, f"Still on login page after submit: {resp.url}"

    # Protected pages must be accessible
    resp = s.get(f"{admin_url}/jobs", timeout=10)
    assert resp.status_code == 200, f"/jobs returned {resp.status_code}"

    resp = s.get(f"{admin_url}/users", timeout=10)
    assert resp.status_code == 200, f"/users returned {resp.status_code}"

    # Logout
    resp = s.get(f"{admin_url}/logout", allow_redirects=True, timeout=10)
    assert resp.status_code == 200

    # After logout, /jobs must redirect to /login
    resp = s.get(f"{admin_url}/jobs", allow_redirects=False, timeout=10)
    assert resp.status_code in (302, 303), "Expected redirect to /login after logout"


# ── Flow 3: Watch a job, verify in watched list, unwatch ──────────────────────


def test_watch_job_flow(backend_url, admin_api_token, user_api_token):
    """Admin creates job → regular user watches it → appears in watched list → unwatch."""
    # Create an active job (admin)
    resp = requests.post(
        f"{backend_url}/api/v1/admin/jobs",
        json={
            "job_title": f"Watch Flow Job {uuid.uuid4().hex[:8]}",
            "organization": "Watch Test Org",
            "qualification_level": "graduate",
            "total_vacancies": 5,
            "description": "Job for watch E2E test.",
            "status": "active",
        },
        headers=_auth(admin_api_token),
        timeout=10,
    )
    assert resp.status_code == 201
    job_id = resp.json()["id"]

    # Watch the job (regular user)
    resp = requests.post(
        f"{backend_url}/api/v1/jobs/{job_id}/watch",
        headers=_auth(user_api_token),
        timeout=10,
    )
    assert resp.status_code == 200
    assert resp.json()["watching"] is True

    # Idempotency: watching again must not error
    resp = requests.post(
        f"{backend_url}/api/v1/jobs/{job_id}/watch",
        headers=_auth(user_api_token),
        timeout=10,
    )
    assert resp.status_code == 200
    assert "already" in resp.json()["message"].lower()

    # Job must appear in /users/me/watched
    resp = requests.get(
        f"{backend_url}/api/v1/users/me/watched",
        headers=_auth(user_api_token),
        timeout=10,
    )
    assert resp.status_code == 200
    watched_ids = [j["id"] for j in resp.json().get("jobs", [])]
    assert job_id in watched_ids

    # Unwatch
    resp = requests.delete(
        f"{backend_url}/api/v1/jobs/{job_id}/watch",
        headers=_auth(user_api_token),
        timeout=10,
    )
    assert resp.status_code == 200
    assert resp.json()["watching"] is False

    # Must no longer appear in watched list
    resp = requests.get(
        f"{backend_url}/api/v1/users/me/watched",
        headers=_auth(user_api_token),
        timeout=10,
    )
    assert resp.status_code == 200
    watched_ids = [j["id"] for j in resp.json().get("jobs", [])]
    assert job_id not in watched_ids

    # Cleanup (admin)
    requests.delete(
        f"{backend_url}/api/v1/admin/jobs/{job_id}",
        headers=_auth(admin_api_token),
        timeout=10,
    )


# ── Flow 4: Entrance exam lifecycle ───────────────────────────────────────────


def test_entrance_exam_lifecycle(backend_url, admin_api_token, user_api_token):
    """Admin creates exam → appears in public list → update → user watches → delete."""
    exam_name = f"E2E Exam {uuid.uuid4().hex[:8]}"

    # Create exam
    resp = requests.post(
        f"{backend_url}/api/v1/admin/entrance-exams",
        json={
            "exam_name": exam_name,
            "conducting_body": "NTA",
            "stream": "engineering",
            "status": "active",
        },
        headers=_auth(admin_api_token),
        timeout=10,
    )
    assert resp.status_code == 201, f"Exam creation failed: {resp.text}"
    exam_id = resp.json()["id"]
    assert resp.json()["slug"]

    # Must appear in public list
    resp = requests.get(f"{backend_url}/api/v1/entrance-exams", timeout=10)
    assert resp.status_code == 200
    public_ids = [e["id"] for e in resp.json().get("data", [])]
    assert exam_id in public_ids

    # Public detail must be accessible
    resp = requests.get(f"{backend_url}/api/v1/entrance-exams/{exam_id}", timeout=10)
    assert resp.status_code == 200
    assert resp.json()["exam_name"] == exam_name

    # Update
    resp = requests.put(
        f"{backend_url}/api/v1/admin/entrance-exams/{exam_id}",
        json={"status": "active"},
        headers=_auth(admin_api_token),
        timeout=10,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"

    # Watch the exam (regular user)
    resp = requests.post(
        f"{backend_url}/api/v1/entrance-exams/{exam_id}/watch",
        headers=_auth(user_api_token),
        timeout=10,
    )
    assert resp.status_code == 200
    assert resp.json()["watching"] is True

    # Verify in watched list
    resp = requests.get(
        f"{backend_url}/api/v1/users/me/watched",
        headers=_auth(user_api_token),
        timeout=10,
    )
    assert resp.status_code == 200
    watched_ids = [e["id"] for e in resp.json().get("exams", [])]
    assert exam_id in watched_ids

    # Delete exam
    resp = requests.delete(
        f"{backend_url}/api/v1/admin/entrance-exams/{exam_id}",
        headers=_auth(admin_api_token),
        timeout=10,
    )
    assert resp.status_code == 204

    # Must no longer appear in public list
    resp = requests.get(f"{backend_url}/api/v1/entrance-exams", timeout=10)
    public_ids = [e["id"] for e in resp.json().get("data", [])]
    assert exam_id not in public_ids
