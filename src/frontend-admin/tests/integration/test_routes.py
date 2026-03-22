"""Integration tests for admin frontend Flask routes.

Uses Flask test client with a mocked ApiClient so no real backend is needed.
"""

import pytest
from unittest.mock import MagicMock
import io


def _ok(json_data=None):
    r = MagicMock()
    r.ok = True
    r.json.return_value = json_data or {}
    r.headers = {"content-type": "application/json"}
    return r


def _fail(json_data=None):
    r = MagicMock()
    r.ok = False
    r.json.return_value = json_data or {"detail": "Error"}
    r.headers = {"content-type": "application/json"}
    return r


# ─── health ───────────────────────────────────────────────────────────────────

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["service"] == "hermes-frontend-admin"


# ─── /login ───────────────────────────────────────────────────────────────────

def test_login_get(client):
    resp = client.get("/login")
    assert resp.status_code == 200


def test_login_post_success(client, mock_api):
    mock_api.post.return_value = _ok({
        "access_token": "jwt",
        "admin": {"full_name": "Admin", "role": "admin"},
    })
    resp = client.post("/login", data={"email": "admin@test.com", "password": "pass"})
    assert resp.status_code == 302
    assert "/" == resp.headers["Location"] or resp.headers["Location"].endswith("/")


def test_login_post_failure(client, mock_api):
    mock_api.post.return_value = _fail()
    resp = client.post("/login", data={"email": "bad@test.com", "password": "wrong"})
    assert resp.status_code == 200
    assert b"Invalid" in resp.data


def test_login_stores_role_in_session(client, mock_api, app):
    mock_api.post.return_value = _ok({
        "access_token": "jwt",
        "admin": {"full_name": "Op", "role": "operator"},
    })
    with app.test_client() as c:
        c.post("/login", data={"email": "op@test.com", "password": "pass"})
        with c.session_transaction() as sess:
            assert sess.get("admin_role") == "operator"


# ─── /logout ──────────────────────────────────────────────────────────────────

def test_logout_redirects_to_login(auth_client):
    client, mock_api = auth_client
    mock_api.post.return_value = _ok()
    resp = client.get("/logout")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_logout_clears_session(auth_client):
    client, mock_api = auth_client
    mock_api.post.return_value = _ok()
    client.get("/logout")
    with client.session_transaction() as sess:
        assert "token" not in sess


def test_logout_calls_backend(auth_client):
    client, mock_api = auth_client
    mock_api.post.return_value = _ok()
    client.get("/logout")
    mock_api.post.assert_called_once_with("/auth/admin/logout", token="admin-token")


def test_logout_no_token_skips_backend(client, mock_api):
    """Logout without a session token should not call backend."""
    resp = client.get("/logout")
    assert resp.status_code == 302
    mock_api.post.assert_not_called()


# ─── / (dashboard) ────────────────────────────────────────────────────────────

def test_dashboard_no_token_redirects(client, mock_api):
    resp = client.get("/")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_dashboard_with_token(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({
        "jobs": {"total": 10, "active": 7, "draft": 3},
        "users": {"total": 100, "active": 90, "new_this_week": 5},
        "applications": {"total": 50},
    })
    resp = client.get("/")
    assert resp.status_code == 200


def test_dashboard_api_failure(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _fail()
    resp = client.get("/")
    assert resp.status_code == 200


# ─── /jobs ────────────────────────────────────────────────────────────────────

def test_jobs_no_token(client, mock_api):
    resp = client.get("/jobs")
    assert resp.status_code == 302


def test_jobs_list(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({"data": [], "pagination": {}})
    resp = client.get("/jobs")
    assert resp.status_code == 200


def test_jobs_with_status_filter(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({"data": [], "pagination": {}})
    resp = client.get("/jobs?status=draft")
    assert resp.status_code == 200
    call_kwargs = mock_api.get.call_args[1]
    assert call_kwargs["params"]["status"] == "draft"


def test_jobs_api_failure(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _fail()
    resp = client.get("/jobs")
    assert resp.status_code == 200


# ─── /jobs/list (HTMX partial) ────────────────────────────────────────────────

def test_jobs_list_partial_no_token(client, mock_api):
    resp = client.get("/jobs/list")
    assert resp.status_code == 401


def test_jobs_list_partial(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({"data": [], "pagination": {}})
    resp = client.get("/jobs/list?offset=20")
    assert resp.status_code == 200
    assert mock_api.get.call_args[1]["params"]["offset"] == 20


def test_jobs_list_partial_with_status(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({"data": [], "pagination": {}})
    resp = client.get("/jobs/list?status=active")
    assert resp.status_code == 200
    assert mock_api.get.call_args[1]["params"]["status"] == "active"


# ─── /jobs/<id>/approve ───────────────────────────────────────────────────────

def test_approve_job_no_token(client, mock_api):
    resp = client.post("/jobs/abc/approve")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_approve_job(auth_client):
    client, mock_api = auth_client
    mock_api.put.return_value = _ok()
    resp = client.post("/jobs/job-123/approve")
    assert resp.status_code == 302
    mock_api.put.assert_called_once_with("/admin/jobs/job-123/approve", token="admin-token")


# ─── /jobs/upload ─────────────────────────────────────────────────────────────

def test_upload_pdf_get_no_token(client, mock_api):
    resp = client.get("/jobs/upload")
    assert resp.status_code == 302


def test_upload_pdf_get(auth_client):
    client, mock_api = auth_client
    resp = client.get("/jobs/upload")
    assert resp.status_code == 200


def test_upload_pdf_no_file(auth_client):
    client, mock_api = auth_client
    resp = client.post("/jobs/upload", data={})
    assert resp.status_code == 200
    assert b"Please select" in resp.data or b"select" in resp.data.lower()


def test_upload_pdf_success(auth_client):
    client, mock_api = auth_client
    mock_api.post_file.return_value = _ok({"task_id": "abc123def456", "filename": "test.pdf"})
    data = {"pdf_file": (io.BytesIO(b"%PDF-1.4 content"), "test.pdf")}
    resp = client.post("/jobs/upload", data=data, content_type="multipart/form-data")
    assert resp.status_code == 302
    assert "draft" in resp.headers["Location"]


def test_upload_pdf_backend_error(auth_client):
    client, mock_api = auth_client
    fail = MagicMock()
    fail.ok = False
    fail.json.return_value = {"detail": "Only PDF files are accepted"}
    fail.headers = {"content-type": "application/json"}
    mock_api.post_file.return_value = fail
    data = {"pdf_file": (io.BytesIO(b"content"), "test.pdf")}
    resp = client.post("/jobs/upload", data=data, content_type="multipart/form-data")
    assert resp.status_code == 200


# ─── /jobs/<id>/review ────────────────────────────────────────────────────────

def test_review_job_get_no_token(client, mock_api):
    resp = client.get("/jobs/job-1/review")
    assert resp.status_code == 302


def test_review_job_get_not_found(auth_client):
    client, mock_api = auth_client
    not_found = MagicMock()
    not_found.ok = False
    mock_api.get.return_value = not_found
    resp = client.get("/jobs/nonexistent/review")
    assert resp.status_code == 302
    assert "/jobs" in resp.headers["Location"]


def test_review_job_get_found(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({
        "id": "job-1", "job_title": "Test Job", "status": "draft",
        "organization": "SSC", "slug": "test-job",
    })
    resp = client.get("/jobs/job-1/review")
    assert resp.status_code == 200
    assert b"Test Job" in resp.data


def test_review_job_post_save(auth_client):
    client, mock_api = auth_client
    mock_api.put.return_value = _ok()
    resp = client.post("/jobs/job-1/review", data={
        "action": "save",
        "job_title": "Updated Title",
        "organization": "SSC",
    })
    assert resp.status_code == 302
    assert "review" in resp.headers["Location"]


def test_review_job_post_approve(auth_client):
    client, mock_api = auth_client
    mock_api.put.return_value = _ok()
    resp = client.post("/jobs/job-1/review", data={
        "action": "approve",
        "job_title": "Final Title",
    })
    assert resp.status_code == 302
    assert "active" in resp.headers["Location"]


# ─── /users ───────────────────────────────────────────────────────────────────

def test_users_no_token(client, mock_api):
    resp = client.get("/users")
    assert resp.status_code == 302


def test_users_list(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({"data": [], "pagination": {}})
    resp = client.get("/users")
    assert resp.status_code == 200


def test_users_with_search(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({"data": [], "pagination": {}})
    resp = client.get("/users?q=test&status=active")
    assert resp.status_code == 200
    call_kwargs = mock_api.get.call_args[1]
    assert call_kwargs["params"]["q"] == "test"
    assert call_kwargs["params"]["status"] == "active"


# ─── /users/list (HTMX partial) ───────────────────────────────────────────────

def test_users_list_partial_no_token(client, mock_api):
    resp = client.get("/users/list")
    assert resp.status_code == 401


def test_users_list_partial(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({"data": [], "pagination": {}})
    resp = client.get("/users/list?offset=20&q=foo")
    assert resp.status_code == 200
    call_kwargs = mock_api.get.call_args[1]
    assert call_kwargs["params"]["offset"] == 20
    assert call_kwargs["params"]["q"] == "foo"


# ─── /users/<id>/suspend ──────────────────────────────────────────────────────

def test_toggle_user_status_no_token(client, mock_api):
    resp = client.post("/users/user-1/suspend")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_suspend_user(auth_client):
    client, mock_api = auth_client
    mock_api.put.return_value = _ok()
    resp = client.post("/users/user-1/suspend", data={"status": "suspended"})
    assert resp.status_code == 302
    mock_api.put.assert_called_once_with(
        "/admin/users/user-1/status",
        token="admin-token",
        json={"status": "suspended"},
    )


def test_activate_user(auth_client):
    client, mock_api = auth_client
    mock_api.put.return_value = _ok()
    resp = client.post("/users/user-1/suspend", data={"status": "active"})
    assert resp.status_code == 302
    assert mock_api.put.call_args[1]["json"] == {"status": "active"}


# ─── /logs ────────────────────────────────────────────────────────────────────

def test_logs_no_token(client, mock_api):
    resp = client.get("/logs")
    assert resp.status_code == 302


def test_logs_list(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({"data": [], "pagination": {}})
    resp = client.get("/logs")
    assert resp.status_code == 200


def test_logs_api_failure(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _fail()
    resp = client.get("/logs")
    assert resp.status_code == 200


# ─── /logs/list (HTMX partial) ────────────────────────────────────────────────

def test_logs_list_partial_no_token(client, mock_api):
    resp = client.get("/logs/list")
    assert resp.status_code == 401


def test_logs_list_partial(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({"data": [], "pagination": {}})
    resp = client.get("/logs/list?offset=20")
    assert resp.status_code == 200
    assert mock_api.get.call_args[1]["params"]["offset"] == 20
