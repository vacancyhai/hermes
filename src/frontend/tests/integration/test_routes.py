"""Integration tests for user frontend Flask routes.

Uses Flask test client with a mocked ApiClient so no real backend is needed.
"""

import pytest
from unittest.mock import MagicMock


def _ok(json_data):
    """Build a mock response that is ok=True and returns json_data."""
    r = MagicMock()
    r.ok = True
    r.json.return_value = json_data
    return r


def _fail():
    """Build a mock response that is ok=False."""
    r = MagicMock()
    r.ok = False
    return r


# ─── health ───────────────────────────────────────────────────────────────────

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


# ─── index ────────────────────────────────────────────────────────────────────

def test_index_renders_jobs(client, mock_api):
    mock_api.get.return_value = _ok({
        "data": [{"id": "1", "job_title": "SSC CGL", "slug": "ssc-cgl", "organization": "SSC",
                  "status": "active", "job_type": "latest_job", "is_featured": False,
                  "is_urgent": False, "created_at": "2026-01-01T00:00:00"}],
        "pagination": {"total": 1, "has_more": False},
    })
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"SSC CGL" in resp.data


def test_index_api_failure_shows_empty(client, mock_api):
    mock_api.get.return_value = _fail()
    resp = client.get("/")
    assert resp.status_code == 200


def test_index_with_filter_params(client, mock_api):
    mock_api.get.return_value = _ok({"data": [], "pagination": {}})
    resp = client.get("/?q=UPSC&job_type=latest_job&limit=10&offset=0")
    assert resp.status_code == 200
    call_kwargs = mock_api.get.call_args[1]
    assert call_kwargs["params"]["q"] == "UPSC"
    assert call_kwargs["params"]["limit"] == 10


# ─── /jobs (HTMX partial) ─────────────────────────────────────────────────────

def test_job_list_partial(client, mock_api):
    mock_api.get.return_value = _ok({"data": [], "pagination": {}})
    resp = client.get("/jobs")
    assert resp.status_code == 200


# ─── /jobs/<slug> ─────────────────────────────────────────────────────────────

def test_job_detail_found(client, mock_api):
    mock_api.get.return_value = _ok({
        "id": "1", "job_title": "UPSC IAS", "slug": "upsc-ias",
        "organization": "UPSC", "status": "active",
    })
    resp = client.get("/jobs/upsc-ias")
    assert resp.status_code == 200
    assert b"UPSC IAS" in resp.data


def test_job_detail_not_found(client, mock_api):
    mock_api.get.return_value = _fail()
    resp = client.get("/jobs/nonexistent")
    assert resp.status_code == 404


# ─── /login ───────────────────────────────────────────────────────────────────

def test_login_get(client):
    resp = client.get("/login")
    assert resp.status_code == 200


def test_login_post_success(client, mock_api):
    mock_api.post.return_value = _ok({
        "access_token": "jwt-token",
        "user": {"full_name": "Test User"},
    })
    resp = client.post("/login", data={"email": "u@test.com", "password": "pass", "next": "/dashboard"})
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]


def test_login_post_failure(client, mock_api):
    mock_api.post.return_value = _fail()
    resp = client.post("/login", data={"email": "u@test.com", "password": "wrong"})
    assert resp.status_code == 200
    assert b"Invalid" in resp.data


# ─── /logout ──────────────────────────────────────────────────────────────────

def test_logout_clears_session(auth_client):
    client, _ = auth_client
    resp = client.get("/logout")
    assert resp.status_code == 302
    assert "/" in resp.headers["Location"]
    with client.session_transaction() as sess:
        assert "token" not in sess


# ─── /dashboard ───────────────────────────────────────────────────────────────

def test_dashboard_no_token_shows_login(client, mock_api):
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert b"login" in resp.data.lower()


def test_dashboard_with_token(auth_client):
    client, mock_api = auth_client
    mock_api.get.side_effect = [
        _ok({"total": 5, "applied": 3}),               # stats
        _ok({"data": [], "pagination": {}}),            # applications
    ]
    resp = client.get("/dashboard")
    assert resp.status_code == 200


def test_dashboard_with_status_filter(auth_client):
    client, mock_api = auth_client
    mock_api.get.side_effect = [
        _ok({"total": 2}),
        _ok({"data": [], "pagination": {}}),
    ]
    resp = client.get("/dashboard?status=applied")
    assert resp.status_code == 200
    # verify status param was passed to applications call
    second_call = mock_api.get.call_args_list[1]
    assert second_call[1]["params"].get("status") == "applied"


def test_dashboard_api_failure(auth_client):
    client, mock_api = auth_client
    mock_api.get.side_effect = [_fail(), _fail()]
    resp = client.get("/dashboard")
    assert resp.status_code == 200


# ─── /dashboard/applications (HTMX partial) ───────────────────────────────────

def test_dashboard_applications_no_token(client, mock_api):
    resp = client.get("/dashboard/applications")
    assert resp.status_code == 401


def test_dashboard_applications_partial(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({"data": [], "pagination": {}})
    resp = client.get("/dashboard/applications?offset=20")
    assert resp.status_code == 200


def test_dashboard_applications_with_status(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({"data": [], "pagination": {}})
    resp = client.get("/dashboard/applications?status=selected")
    assert resp.status_code == 200
    call_kwargs = mock_api.get.call_args[1]
    assert call_kwargs["params"]["status"] == "selected"


# ─── /notifications ───────────────────────────────────────────────────────────

def test_notifications_no_token(client, mock_api):
    resp = client.get("/notifications")
    assert resp.status_code == 200
    assert b"login" in resp.data.lower()


def test_notifications_with_token(auth_client):
    client, mock_api = auth_client
    mock_api.get.side_effect = [
        _ok({"count": 3}),
        _ok({"data": [], "pagination": {}}),
    ]
    resp = client.get("/notifications")
    assert resp.status_code == 200


def test_notifications_api_failure(auth_client):
    client, mock_api = auth_client
    mock_api.get.side_effect = [_fail(), _fail()]
    resp = client.get("/notifications")
    assert resp.status_code == 200


# ─── /notifications/list (HTMX partial) ───────────────────────────────────────

def test_notifications_list_no_token(client, mock_api):
    resp = client.get("/notifications/list")
    assert resp.status_code == 401


def test_notifications_list_empty(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({"data": [], "pagination": {"has_more": False}})
    resp = client.get("/notifications/list")
    assert resp.status_code == 200


def test_notifications_list_with_items(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({
        "data": [{"id": "n1", "title": "New Job", "message": "SSC CGL posted",
                  "is_read": False, "created_at": "2026-01-01T12:00:00"}],
        "pagination": {"has_more": False},
    })
    resp = client.get("/notifications/list")
    assert resp.status_code == 200
    assert b"New Job" in resp.data


def test_notifications_list_has_more(auth_client):
    """When has_more=True, response includes a Load more button."""
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({
        "data": [{"id": "n1", "title": "T", "message": "M",
                  "is_read": True, "created_at": "2026-01-01T00:00:00"}],
        "pagination": {"has_more": True},
    })
    resp = client.get("/notifications/list?offset=0")
    assert b"Load more" in resp.data


# ─── /notifications/unread-count ──────────────────────────────────────────────

def test_unread_count_no_token(client, mock_api):
    resp = client.get("/notifications/unread-count")
    assert resp.status_code == 200
    assert resp.data == b""


def test_unread_count_zero(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({"count": 0})
    resp = client.get("/notifications/unread-count")
    assert resp.data == b""


def test_unread_count_nonzero(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({"count": 5})
    resp = client.get("/notifications/unread-count")
    assert resp.data == b"5"


# ─── /notifications/<id>/read ─────────────────────────────────────────────────

def test_mark_notification_read_no_token(client, mock_api):
    resp = client.post("/notifications/abc/read")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_mark_notification_read(auth_client):
    client, mock_api = auth_client
    mock_api.put.return_value = _ok({})
    resp = client.post("/notifications/abc/read")
    assert resp.status_code == 302
    mock_api.put.assert_called_once_with("/notifications/abc/read", token="test-token")


# ─── /notifications/read-all ──────────────────────────────────────────────────

def test_mark_all_read_no_token(client, mock_api):
    resp = client.post("/notifications/read-all")
    assert resp.status_code == 302


def test_mark_all_read(auth_client):
    client, mock_api = auth_client
    mock_api.put.return_value = _ok({})
    resp = client.post("/notifications/read-all")
    assert resp.status_code == 302
    mock_api.put.assert_called_once_with("/notifications/read-all", token="test-token")


# ─── /notifications/<id>/delete ───────────────────────────────────────────────

def test_delete_notification_no_token(client, mock_api):
    resp = client.post("/notifications/abc/delete")
    assert resp.status_code == 302


def test_delete_notification(auth_client):
    client, mock_api = auth_client
    mock_api.delete.return_value = _ok({})
    resp = client.post("/notifications/abc/delete")
    assert resp.status_code == 302
    mock_api.delete.assert_called_once_with("/notifications/abc", token="test-token")


# ─── /offline ─────────────────────────────────────────────────────────────────

def test_offline_page(client):
    resp = client.get("/offline")
    assert resp.status_code == 200
