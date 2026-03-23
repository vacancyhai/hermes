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


def _set_csrf(client, token="test-csrf"):
    """Set a CSRF token in the session so POST forms pass validation."""
    with client.session_transaction() as sess:
        sess["csrf_token"] = token
    return token


# ─── health ───────────────────────────────────────────────────────────────────

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["service"] == "hermes-frontend-admin"


# ─── /login ───────────────────────────────────────────────────────────────────

def test_login_get(client):
    resp = client.get("/login")
    assert resp.status_code == 200


def test_login_get_sets_csrf_in_session(client):
    client.get("/login")
    with client.session_transaction() as sess:
        assert "csrf_token" in sess


def test_login_post_no_csrf_redirects(client, mock_api):
    """POST without CSRF token should redirect back to /login."""
    resp = client.post("/login", data={"email": "admin@test.com", "password": "pass"})
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
    mock_api.post.assert_not_called()


def test_login_post_wrong_csrf_redirects(client, mock_api):
    """POST with wrong CSRF token should redirect back to /login."""
    _set_csrf(client, "correct-token")
    resp = client.post("/login", data={
        "email": "admin@test.com", "password": "pass", "csrf_token": "wrong-token"
    })
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
    mock_api.post.assert_not_called()


def test_login_post_success(client, mock_api):
    _set_csrf(client, "tok")
    mock_api.post.return_value = _ok({
        "access_token": "jwt.payload.sig",
        "refresh_token": "refresh-tok",
    })
    resp = client.post("/login", data={
        "email": "admin@test.com", "password": "pass", "csrf_token": "tok"
    })
    assert resp.status_code == 302
    loc = resp.headers["Location"]
    assert loc == "/" or loc.endswith("/")


def test_login_post_failure(client, mock_api):
    _set_csrf(client, "tok")
    mock_api.post.return_value = _fail()
    resp = client.post("/login", data={
        "email": "bad@test.com", "password": "wrong", "csrf_token": "tok"
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Invalid" in resp.data


def test_login_stores_role_in_session(client, mock_api, app):
    # "jwt" has no dots → _jwt_payload returns {} → role defaults to "operator"
    mock_api.post.return_value = _ok({
        "access_token": "jwt",
        "refresh_token": "ref",
    })
    with app.test_client() as c:
        _set_csrf(c, "tok")
        c.post("/login", data={"email": "op@test.com", "password": "pass", "csrf_token": "tok"})
        with c.session_transaction() as sess:
            assert sess.get("admin_role") == "operator"


def test_login_stores_admin_role_from_jwt(client, mock_api, app):
    """A JWT with role=admin in payload should store admin_role=admin."""
    import base64, json
    payload = base64.urlsafe_b64encode(json.dumps({"role": "admin"}).encode()).decode().rstrip("=")
    mock_api.post.return_value = _ok({
        "access_token": f"header.{payload}.sig",
        "refresh_token": "ref",
    })
    with app.test_client() as c:
        _set_csrf(c, "tok")
        c.post("/login", data={"email": "admin@test.com", "password": "pass", "csrf_token": "tok"})
        with c.session_transaction() as sess:
            assert sess.get("admin_role") == "admin"


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


def test_dashboard_admin_fetches_analytics(app, mock_api):
    """Admin role triggers extra /admin/analytics call."""
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess["token"] = "admin-token"
            sess["admin_role"] = "admin"

        stats = _ok({"jobs": {}, "users": {}, "applications": {}})
        analytics = _ok({
            "application_statuses": {},
            "top_organizations": [],
            "user_categories": {},
            "user_qualifications": {},
        })
        mock_api.get.side_effect = [stats, analytics]

        resp = c.get("/")
        assert resp.status_code == 200
        assert mock_api.get.call_count == 2
        calls = [call[0][0] for call in mock_api.get.call_args_list]
        assert "/admin/analytics" in calls


def test_dashboard_operator_skips_analytics(app, mock_api):
    """Operator role should NOT call /admin/analytics."""
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess["token"] = "op-token"
            sess["admin_role"] = "operator"

        mock_api.get.return_value = _ok({"jobs": {}, "users": {}, "applications": {}})

        resp = c.get("/")
        assert resp.status_code == 200
        assert mock_api.get.call_count == 1
        assert mock_api.get.call_args[0][0] == "/admin/stats"


def test_dashboard_401_triggers_refresh(app, mock_api):
    """A 401 on stats should attempt token refresh before retrying."""
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess["token"] = "expired-token"
            sess["refresh_token"] = "refresh-tok"
            sess["admin_role"] = "operator"

        expired = MagicMock()
        expired.ok = False
        expired.status_code = 401

        refreshed = MagicMock()
        refreshed.ok = True
        refreshed.json.return_value = {"access_token": "new-token", "refresh_token": "new-ref"}

        stats_ok = _ok({"jobs": {}, "users": {}, "applications": {}})

        mock_api.get.side_effect = [expired, stats_ok]
        mock_api.post.return_value = refreshed

        resp = c.get("/")
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


# ─── /jobs/new ────────────────────────────────────────────────────────────────

def test_new_job_get_no_token(client, mock_api):
    resp = client.get("/jobs/new")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_new_job_get(auth_client):
    client, mock_api = auth_client
    resp = client.get("/jobs/new")
    assert resp.status_code == 200
    assert b"job_title" in resp.data or b"Job Title" in resp.data


def test_new_job_post_success(auth_client):
    client, mock_api = auth_client
    mock_api.post.return_value = _ok({"id": "new-job-123"})
    resp = client.post("/jobs/new", data={
        "job_title": "Test Job",
        "organization": "SSC",
        "status": "draft",
    })
    assert resp.status_code == 302
    assert "new-job-123" in resp.headers["Location"]


def test_new_job_post_int_fields(auth_client):
    """Integer and date fields should be correctly parsed."""
    client, mock_api = auth_client
    mock_api.post.return_value = _ok({"id": "job-abc"})
    client.post("/jobs/new", data={
        "job_title": "Job",
        "organization": "SSC",
        "total_vacancies": "100",
        "fee_general": "500",
        "salary_initial": "300000",
        "status": "draft",
    })
    payload = mock_api.post.call_args[1]["json"]
    assert payload["total_vacancies"] == 100
    assert payload["fee_general"] == 500
    assert payload["salary_initial"] == 300000


def test_new_job_post_empty_int_becomes_none(auth_client):
    client, mock_api = auth_client
    mock_api.post.return_value = _ok({"id": "job-abc"})
    client.post("/jobs/new", data={
        "job_title": "Job",
        "organization": "SSC",
        "total_vacancies": "",
        "status": "draft",
    })
    payload = mock_api.post.call_args[1]["json"]
    assert payload["total_vacancies"] is None


def test_new_job_post_failure(auth_client):
    client, mock_api = auth_client
    mock_api.post.return_value = _fail({"detail": "Validation error"})
    resp = client.post("/jobs/new", data={
        "job_title": "Job",
        "organization": "SSC",
        "status": "draft",
    })
    assert resp.status_code == 200
    assert b"Validation error" in resp.data or b"error" in resp.data.lower()


# ─── /jobs/<id>/delete ────────────────────────────────────────────────────────

def test_delete_job_no_token(client, mock_api):
    resp = client.post("/jobs/job-1/delete")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
    mock_api.delete.assert_not_called()


def test_delete_job(auth_client):
    client, mock_api = auth_client
    mock_api.delete.return_value = _ok()
    resp = client.post("/jobs/job-1/delete")
    assert resp.status_code == 302
    assert "/jobs" in resp.headers["Location"]
    mock_api.delete.assert_called_once_with("/admin/jobs/job-1", token="admin-token")


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
    assert b"select" in resp.data.lower()


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


def test_review_job_post_int_fields_parsed(auth_client):
    client, mock_api = auth_client
    mock_api.put.return_value = _ok()
    client.post("/jobs/job-1/review", data={
        "action": "save",
        "job_title": "Job",
        "total_vacancies": "50",
        "fee_general": "200",
    })
    put_call = mock_api.put.call_args_list[0]
    payload = put_call[1]["json"]
    assert payload["total_vacancies"] == 50
    assert payload["fee_general"] == 200


def test_review_job_post_empty_int_becomes_none(auth_client):
    client, mock_api = auth_client
    mock_api.put.return_value = _ok()
    client.post("/jobs/job-1/review", data={
        "action": "save",
        "job_title": "Job",
        "total_vacancies": "",
    })
    put_call = mock_api.put.call_args_list[0]
    payload = put_call[1]["json"]
    assert payload["total_vacancies"] is None


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


# ─── /users/<id> ──────────────────────────────────────────────────────────────

def test_user_detail_no_token(client, mock_api):
    resp = client.get("/users/user-1")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_user_detail_not_found(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _fail()
    resp = client.get("/users/nonexistent")
    assert resp.status_code == 302
    assert "/users" in resp.headers["Location"]


def test_user_detail_found(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({
        "id": "user-1",
        "full_name": "John Doe",
        "email": "john@example.com",
        "status": "active",
        "is_email_verified": True,
        "created_at": "2025-01-01T00:00:00",
        "profile": {
            "gender": "male",
            "category": "general",
            "state": "Delhi",
        },
    })
    resp = client.get("/users/user-1")
    assert resp.status_code == 200
    assert b"John Doe" in resp.data


def test_user_detail_shows_profile_data(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({
        "id": "user-2",
        "full_name": "Jane Smith",
        "email": "jane@example.com",
        "status": "suspended",
        "is_email_verified": False,
        "created_at": "2025-06-15T10:00:00",
        "profile": {"gender": "female", "category": "obc", "state": "UP"},
    })
    resp = client.get("/users/user-2")
    assert resp.status_code == 200
    assert b"Jane Smith" in resp.data
    assert b"suspended" in resp.data.lower() or b"Suspended" in resp.data


def test_user_detail_no_profile(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({
        "id": "user-3",
        "full_name": "No Profile",
        "email": "np@example.com",
        "status": "active",
        "is_email_verified": False,
        "created_at": None,
        "profile": {},
    })
    resp = client.get("/users/user-3")
    assert resp.status_code == 200


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


# ─── /users/<id>/role ─────────────────────────────────────────────────────────

def test_change_user_role_no_token(client, mock_api):
    resp = client.post("/users/user-1/role", data={"role": "admin"})
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]
    mock_api.put.assert_not_called()


def test_change_user_role(auth_client):
    client, mock_api = auth_client
    mock_api.put.return_value = _ok()
    resp = client.post("/users/user-1/role", data={"role": "admin"})
    assert resp.status_code == 302
    assert "/users/user-1" in resp.headers["Location"]
    mock_api.put.assert_called_once_with(
        "/admin/users/user-1/role",
        token="admin-token",
        json={"role": "admin"},
    )


def test_change_user_role_to_operator(auth_client):
    client, mock_api = auth_client
    mock_api.put.return_value = _ok()
    client.post("/users/user-1/role", data={"role": "operator"})
    assert mock_api.put.call_args[1]["json"] == {"role": "operator"}


def test_change_user_role_empty_skips_api(auth_client):
    """Empty role value should not call the backend."""
    client, mock_api = auth_client
    resp = client.post("/users/user-1/role", data={"role": ""})
    assert resp.status_code == 302
    mock_api.put.assert_not_called()


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
