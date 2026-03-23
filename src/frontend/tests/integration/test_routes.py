"""Integration tests for user frontend Flask routes.

Uses Flask test client with a mocked ApiClient so no real backend is needed.
"""

import pytest
from unittest.mock import MagicMock


def _ok(json_data=None):
    """Build a mock response that is ok=True and returns json_data."""
    r = MagicMock()
    r.ok = True
    r.status_code = 200
    r.json.return_value = json_data or {}
    r.headers = {"content-type": "application/json"}
    return r


def _fail(status_code=400, json_data=None):
    """Build a mock response that is ok=False."""
    r = MagicMock()
    r.ok = False
    r.status_code = status_code
    r.json.return_value = json_data or {"detail": "Error"}
    r.headers = {"content-type": "application/json"}
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


def test_index_recommended_tab_no_token(client, mock_api):
    """Without a token, ?recommended=1 falls back to normal job listing."""
    mock_api.get.return_value = _ok({"data": [], "pagination": {}})
    resp = client.get("/?recommended=1")
    assert resp.status_code == 200
    called_path = mock_api.get.call_args[0][0]
    assert called_path == "/jobs"


def test_index_recommended_tab_with_token(auth_client):
    """With a token and ?recommended=1, calls /jobs/recommended."""
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({"data": [], "pagination": {}})
    resp = client.get("/?recommended=1")
    assert resp.status_code == 200
    called_path = mock_api.get.call_args[0][0]
    assert called_path == "/jobs/recommended"


# ─── /jobs (HTMX partial) ─────────────────────────────────────────────────────

def test_job_list_partial(client, mock_api):
    mock_api.get.return_value = _ok({"data": [], "pagination": {}})
    resp = client.get("/jobs")
    assert resp.status_code == 200


def test_job_list_partial_recommended(auth_client):
    """?recommended=1 partial uses /jobs/recommended endpoint."""
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({"data": [], "pagination": {}})
    resp = client.get("/jobs?recommended=1")
    assert resp.status_code == 200
    assert mock_api.get.call_args[0][0] == "/jobs/recommended"


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


def test_job_detail_shows_track_button_when_logged_in(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({
        "id": "job-1", "job_title": "SSC CGL", "slug": "ssc-cgl",
        "organization": "SSC", "status": "active",
    })
    resp = client.get("/jobs/ssc-cgl")
    assert resp.status_code == 200
    assert b"Track This Job" in resp.data


def test_job_detail_shows_login_button_when_logged_out(client, mock_api):
    mock_api.get.return_value = _ok({
        "id": "job-1", "job_title": "SSC CGL", "slug": "ssc-cgl",
        "organization": "SSC", "status": "active",
    })
    resp = client.get("/jobs/ssc-cgl")
    assert resp.status_code == 200
    assert b"Login to Track" in resp.data


# ─── /login ───────────────────────────────────────────────────────────────────

def test_login_get(client):
    """Login page renders (GET-only; Firebase JS SDK handles auth client-side)."""
    resp = client.get("/login")
    assert resp.status_code == 200


# ─── /logout ──────────────────────────────────────────────────────────────────

def test_logout_clears_session(auth_client):
    client, _ = auth_client
    resp = client.get("/logout")
    assert resp.status_code == 302
    assert "/" in resp.headers["Location"]
    with client.session_transaction() as sess:
        assert "token" not in sess


# ─── /auth/firebase-callback ──────────────────────────────────────────────────

def test_firebase_callback_success(client, mock_api):
    """Firebase callback verifies token, stores JWT in session, returns redirect."""
    mock_api.post.return_value = _ok({"access_token": "jwt-access", "refresh_token": "jwt-refresh"})
    mock_api.get.return_value = _ok({"full_name": "Firebase User"})
    resp = client.post(
        "/auth/firebase-callback",
        json={"id_token": "valid-firebase-id-token"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["redirect"] == "/dashboard"
    mock_api.post.assert_called_once_with(
        "/auth/verify-token",
        json={"id_token": "valid-firebase-id-token", "full_name": None},
    )
    mock_api.get.assert_called_once_with("/users/profile", token="jwt-access")


def test_firebase_callback_stores_token_in_session(app, mock_api):
    """Tokens returned by backend are stored in Flask session."""
    mock_api.post.return_value = _ok({"access_token": "the-jwt", "refresh_token": "the-ref"})
    mock_api.get.return_value = _ok({"full_name": "User"})
    with app.test_client() as c:
        c.post(
            "/auth/firebase-callback",
            json={"id_token": "tok"},
            content_type="application/json",
        )
        with c.session_transaction() as sess:
            assert sess.get("token") == "the-jwt"
            assert sess.get("refresh_token") == "the-ref"


def test_firebase_callback_missing_token(client, mock_api):
    """Missing id_token returns 400."""
    resp = client.post(
        "/auth/firebase-callback",
        json={},
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_firebase_callback_backend_failure(client, mock_api):
    """Backend 401 is relayed back to the caller."""
    mock_api.post.return_value = _fail(status_code=401, json_data={"detail": "Invalid Firebase token"})
    resp = client.post(
        "/auth/firebase-callback",
        json={"id_token": "bad-token"},
        content_type="application/json",
    )
    assert resp.status_code == 401


def test_firebase_callback_with_full_name(client, mock_api):
    """full_name is forwarded to backend verify-token."""
    mock_api.post.return_value = _ok({"access_token": "tok", "refresh_token": "ref"})
    mock_api.get.return_value = _ok({"full_name": "New User"})
    client.post(
        "/auth/firebase-callback",
        json={"id_token": "tok", "full_name": "New User"},
        content_type="application/json",
    )
    mock_api.post.assert_called_once_with(
        "/auth/verify-token",
        json={"id_token": "tok", "full_name": "New User"},
    )


# ─── /profile ─────────────────────────────────────────────────────────────────

def test_profile_no_token(client, mock_api):
    resp = client.get("/profile")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_profile_get(auth_client):
    client, mock_api = auth_client
    mock_api.get.side_effect = [
        _ok({
            "id": "u1", "email": "u@test.com", "full_name": "Test User",
            "phone": None, "status": "active", "is_email_verified": True,
            "profile": {
                "gender": None, "category": None, "state": None, "city": None,
                "pincode": None, "highest_qualification": "graduate",
                "is_pwd": False, "is_ex_serviceman": False,
                "preferred_states": ["Delhi"], "preferred_categories": ["general"],
                "followed_organizations": [], "notification_preferences": {},
                "fcm_tokens": [],
            },
        }),
        _ok({"followed_organizations": ["UPSC"], "count": 1}),
    ]
    resp = client.get("/profile")
    assert resp.status_code == 200
    assert b"Test User" in resp.data or b"profile" in resp.data.lower()


def test_profile_get_api_failure(auth_client):
    client, mock_api = auth_client
    mock_api.get.side_effect = [_fail(), _fail()]
    resp = client.get("/profile")
    assert resp.status_code == 200


def test_profile_post_update_profile(auth_client):
    client, mock_api = auth_client
    mock_api.put.return_value = _ok({})
    resp = client.post("/profile", data={
        "action": "profile",
        "gender": "Male",
        "state": "Delhi",
        "city": "New Delhi",
        "pincode": "110001",
        "highest_qualification": "graduate",
        "preferred_states": "Delhi, Bihar",
        "preferred_categories": ["general", "obc"],
    })
    assert resp.status_code == 302
    assert "/profile" in resp.headers["Location"]
    mock_api.put.assert_called()
    profile_call = mock_api.put.call_args_list[0]
    assert profile_call[0][0] == "/users/profile"
    assert profile_call[1]["json"]["highest_qualification"] == "graduate"


def test_profile_post_with_phone(auth_client):
    client, mock_api = auth_client
    mock_api.put.return_value = _ok({})
    resp = client.post("/profile", data={
        "action": "profile",
        "phone": "9876543210",
        "preferred_states": "",
    })
    assert resp.status_code == 302
    # Both profile PUT and phone PUT should be called
    put_paths = [c[0][0] for c in mock_api.put.call_args_list]
    assert "/users/profile" in put_paths
    assert "/users/profile/phone" in put_paths


def test_profile_post_notification_prefs(auth_client):
    client, mock_api = auth_client
    mock_api.put.return_value = _ok({})
    resp = client.post("/profile", data={
        "action": "notification_prefs",
        "email_notif": "on",
    })
    assert resp.status_code == 302
    mock_api.put.assert_called_once_with(
        "/users/me/notification-preferences",
        token="test-token",
        json={"email": True, "push": False},
    )


# ─── /profile/follow ──────────────────────────────────────────────────────────

def test_follow_org_no_token(client, mock_api):
    resp = client.post("/profile/follow", data={"org_name": "UPSC"})
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_follow_org(auth_client):
    client, mock_api = auth_client
    mock_api.post.return_value = _ok({"message": "Now following UPSC"})
    resp = client.post("/profile/follow", data={"org_name": "UPSC", "next": "/profile"})
    assert resp.status_code == 302
    mock_api.post.assert_called_once_with("/organizations/UPSC/follow", token="test-token")


def test_follow_org_empty_name_skips_api(auth_client):
    client, mock_api = auth_client
    resp = client.post("/profile/follow", data={"org_name": ""})
    assert resp.status_code == 302
    mock_api.post.assert_not_called()


# ─── /profile/unfollow ────────────────────────────────────────────────────────

def test_unfollow_org_no_token(client, mock_api):
    resp = client.post("/profile/unfollow", data={"org_name": "UPSC"})
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_unfollow_org(auth_client):
    client, mock_api = auth_client
    mock_api.delete.return_value = _ok()
    resp = client.post("/profile/unfollow", data={"org_name": "UPSC", "next": "/jobs/test"})
    assert resp.status_code == 302
    mock_api.delete.assert_called_once_with("/organizations/UPSC/follow", token="test-token")


# ─── /dashboard ───────────────────────────────────────────────────────────────

def test_dashboard_no_token_shows_login(client, mock_api):
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert b"login" in resp.data.lower()


def test_dashboard_with_token(auth_client):
    client, mock_api = auth_client
    mock_api.get.side_effect = [
        _ok({"total": 5, "applied": 3}),
        _ok({"data": [], "pagination": {}}),
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
    second_call = mock_api.get.call_args_list[1]
    assert second_call[1]["params"].get("status") == "applied"


def test_dashboard_api_failure(auth_client):
    client, mock_api = auth_client
    mock_api.get.side_effect = [_fail(), _fail()]
    resp = client.get("/dashboard")
    assert resp.status_code == 200


# ─── /dashboard/track ─────────────────────────────────────────────────────────

def test_track_application_no_token(client, mock_api):
    resp = client.post("/dashboard/track", data={"job_id": "job-1"})
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_track_application_success(auth_client):
    client, mock_api = auth_client
    mock_api.post.return_value = _ok({"id": "app-1", "status": "applied"})
    resp = client.post("/dashboard/track", data={
        "job_id": "job-1", "notes": "Preparing", "is_priority": "on", "next": "/dashboard",
    })
    assert resp.status_code == 302
    mock_api.post.assert_called_once_with(
        "/applications",
        token="test-token",
        json={"job_id": "job-1", "notes": "Preparing", "is_priority": True},
    )


def test_track_application_already_tracked(auth_client):
    client, mock_api = auth_client
    mock_api.post.return_value = _fail(status_code=409)
    resp = client.post("/dashboard/track", data={"job_id": "job-1"})
    assert resp.status_code == 302


def test_track_application_no_notes(auth_client):
    """Empty notes should be sent as None."""
    client, mock_api = auth_client
    mock_api.post.return_value = _ok({"id": "app-1"})
    client.post("/dashboard/track", data={"job_id": "job-1", "notes": ""})
    call_json = mock_api.post.call_args[1]["json"]
    assert call_json["notes"] is None


# ─── /dashboard/applications/<id>/update ──────────────────────────────────────

def test_update_application_no_token(client, mock_api):
    resp = client.post("/dashboard/applications/app-1/update", data={"status": "applied"})
    assert resp.status_code == 401


def test_update_application(auth_client):
    client, mock_api = auth_client
    mock_api.put.return_value = _ok({"id": "app-1", "status": "admit_card_released"})
    resp = client.post("/dashboard/applications/app-1/update", data={
        "status": "admit_card_released",
        "notes": "Received hall ticket",
        "application_number": "UPSC-2026-001",
        "is_priority": "on",
    })
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]
    mock_api.put.assert_called_once()
    call_json = mock_api.put.call_args[1]["json"]
    assert call_json["status"] == "admit_card_released"
    assert call_json["is_priority"] is True


def test_update_application_clears_empty_fields(auth_client):
    """Empty notes and application_number should become None."""
    client, mock_api = auth_client
    mock_api.put.return_value = _ok({})
    client.post("/dashboard/applications/app-1/update", data={
        "status": "applied", "notes": "", "application_number": "",
    })
    call_json = mock_api.put.call_args[1]["json"]
    assert call_json["notes"] is None
    assert call_json["application_number"] is None


# ─── /dashboard/applications/<id>/delete ──────────────────────────────────────

def test_delete_application_no_token(client, mock_api):
    resp = client.post("/dashboard/applications/app-1/delete")
    assert resp.status_code == 401


def test_delete_application(auth_client):
    client, mock_api = auth_client
    mock_api.delete.return_value = _ok()
    resp = client.post("/dashboard/applications/app-1/delete")
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]
    mock_api.delete.assert_called_once_with("/applications/app-1", token="test-token")


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
