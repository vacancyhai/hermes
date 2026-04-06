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

def test_index_redirects_to_dashboard(client):
    """/ redirects to /dashboard."""
    resp = client.get("/")
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]


# ─── /jobs ────────────────────────────────────────────────────────────────────

def test_job_list(client, mock_api):
    mock_api.get.return_value = _ok({"data": [], "pagination": {}})
    resp = client.get("/jobs")
    assert resp.status_code == 200


def test_job_list_with_filter_params(client, mock_api):
    mock_api.get.return_value = _ok({"data": [], "pagination": {}})
    resp = client.get("/jobs?q=UPSC&limit=10&offset=0")
    assert resp.status_code == 200
    call_kwargs = mock_api.get.call_args[1]
    assert call_kwargs["params"]["q"] == "UPSC"
    assert call_kwargs["params"]["limit"] == 10


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


def test_job_detail_logged_in(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({
        "id": "job-1", "job_title": "SSC CGL", "slug": "ssc-cgl",
        "organization": "SSC", "status": "active",
    })
    resp = client.get("/jobs/ssc-cgl")
    assert resp.status_code == 200


def test_job_detail_logged_out(client, mock_api):
    mock_api.get.return_value = _ok({
        "id": "job-1", "job_title": "SSC CGL", "slug": "ssc-cgl",
        "organization": "SSC", "status": "active",
    })
    resp = client.get("/jobs/ssc-cgl")
    assert resp.status_code == 200


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
    assert data["redirect"] == "/"
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


def _set_csrf(client, token="test-csrf"):
    """Set a CSRF token in the session so POST forms pass validation."""
    with client.session_transaction() as sess:
        sess["csrf_token"] = token
    return token


def test_profile_post_update_profile(auth_client):
    client, mock_api = auth_client
    csrf = _set_csrf(client)
    mock_api.put.return_value = _ok({})
    resp = client.post("/profile", data={
        "csrf_token": csrf,
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
    csrf = _set_csrf(client)
    mock_api.put.return_value = _ok({})
    resp = client.post("/profile", data={
        "csrf_token": csrf,
        "action": "profile",
        "phone": "9876543210",
        "preferred_states": "",
    })
    assert resp.status_code == 302
    put_paths = [c[0][0] for c in mock_api.put.call_args_list]
    assert "/users/profile" in put_paths
    assert "/users/profile/phone" in put_paths


def test_profile_post_notification_prefs(auth_client):
    client, mock_api = auth_client
    csrf = _set_csrf(client)
    mock_api.put.return_value = _ok({})
    resp = client.post("/profile", data={
        "csrf_token": csrf,
        "action": "notification_prefs",
        "email_notif": "on",
    })
    assert resp.status_code == 302
    mock_api.put.assert_called_once_with(
        "/users/me/notification-preferences",
        token="test-token",
        json={"email": True, "push": False},
    )


# ─── /dashboard ───────────────────────────────────────────────────────────────

def test_dashboard_no_token_shows_login(client, mock_api):
    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert b"login" in resp.data.lower()


def test_dashboard_with_token(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({"jobs": [], "exams": [], "total": 0})
    resp = client.get("/dashboard")
    assert resp.status_code == 200


def test_dashboard_api_failure(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _fail()
    resp = client.get("/dashboard")
    assert resp.status_code == 200


# ─── /notifications ───────────────────────────────────────────────────────────

def test_notifications_no_token_shows_login(client, mock_api):
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
    """Without token, CSRF also fails — redirects (to referrer or /)."""
    resp = client.post("/notifications/abc/read")
    assert resp.status_code == 302


def test_mark_notification_read(auth_client):
    client, mock_api = auth_client
    csrf = _set_csrf(client)
    mock_api.put.return_value = _ok({})
    resp = client.post("/notifications/abc/read", data={"csrf_token": csrf})
    assert resp.status_code == 302
    mock_api.put.assert_called_once_with("/notifications/abc/read", token="test-token")


# ─── /notifications/read-all ──────────────────────────────────────────────────

def test_mark_all_read_no_token(client, mock_api):
    resp = client.post("/notifications/read-all")
    assert resp.status_code == 302


def test_mark_all_read(auth_client):
    client, mock_api = auth_client
    csrf = _set_csrf(client)
    mock_api.put.return_value = _ok({})
    resp = client.post("/notifications/read-all", data={"csrf_token": csrf})
    assert resp.status_code == 302
    mock_api.put.assert_called_once_with("/notifications/read-all", token="test-token")


# ─── /notifications/<id>/delete ───────────────────────────────────────────────

def test_delete_notification_no_token(client, mock_api):
    resp = client.post("/notifications/abc/delete")
    assert resp.status_code == 302


def test_delete_notification(auth_client):
    client, mock_api = auth_client
    csrf = _set_csrf(client)
    mock_api.delete.return_value = _ok({})
    resp = client.post("/notifications/abc/delete", data={"csrf_token": csrf})
    assert resp.status_code == 302
    mock_api.delete.assert_called_once_with("/notifications/abc", token="test-token")


# ─── /offline ─────────────────────────────────────────────────────────────────

def test_offline_page(client):
    resp = client.get("/offline")
    assert resp.status_code == 200


# ─── /auth/send-email-otp ─────────────────────────────────────────────────────

def test_send_email_otp_success(client, mock_api):
    mock_api.post.return_value = _ok({"message": "OTP sent to your email"})
    resp = client.post(
        "/auth/send-email-otp",
        json={"email": "user@example.com", "full_name": "Test User"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.get_json()["message"] == "OTP sent to your email"


def test_send_email_otp_missing_fields(client, mock_api):
    resp = client.post(
        "/auth/send-email-otp",
        json={"email": "user@example.com"},
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_send_email_otp_backend_failure(client, mock_api):
    mock_api.post.return_value = _fail(503, {"detail": "Email service not configured"})
    resp = client.post(
        "/auth/send-email-otp",
        json={"email": "user@example.com", "full_name": "Test"},
        content_type="application/json",
    )
    assert resp.status_code == 503
    assert "error" in resp.get_json()


# ─── /auth/verify-email-otp ───────────────────────────────────────────────────

def test_verify_email_otp_success(client, mock_api):
    mock_api.post.return_value = _ok({"verified": True, "verification_token": "tok123"})
    resp = client.post(
        "/auth/verify-email-otp",
        json={"email": "user@example.com", "otp": "123456"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.get_json()["verified"] is True


def test_verify_email_otp_missing_fields(client, mock_api):
    resp = client.post(
        "/auth/verify-email-otp",
        json={"email": "user@example.com"},
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_verify_email_otp_backend_failure(client, mock_api):
    mock_api.post.return_value = _fail(400, {"detail": "Invalid OTP"})
    resp = client.post(
        "/auth/verify-email-otp",
        json={"email": "user@example.com", "otp": "000000"},
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


# ─── /auth/complete-registration ──────────────────────────────────────────────

def test_complete_registration_success(client, mock_api):
    mock_api.post.return_value = _ok({"custom_token": "firebase-custom-token"})
    resp = client.post(
        "/auth/complete-registration",
        json={"email": "u@example.com", "password": "pass1234", "verification_token": "vtok"},  # pragma: allowlist secret
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert "custom_token" in resp.get_json()


def test_complete_registration_missing_fields(client, mock_api):
    resp = client.post(
        "/auth/complete-registration",
        json={"email": "u@example.com"},
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_complete_registration_backend_failure(client, mock_api):
    mock_api.post.return_value = _fail(401, {"detail": "Invalid verification token"})
    resp = client.post(
        "/auth/complete-registration",
        json={"email": "u@example.com", "password": "pass1234", "verification_token": "bad"},  # pragma: allowlist secret
        content_type="application/json",
    )
    assert resp.status_code == 401
    assert "error" in resp.get_json()


# ─── /auth/check-user-providers ───────────────────────────────────────────────

def test_check_user_providers_success(client, mock_api):
    mock_api.post.return_value = _ok({"exists": True, "has_password": False})
    resp = client.post(
        "/auth/check-user-providers",
        json={"email": "user@example.com"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.get_json()["exists"] is True


def test_check_user_providers_missing_email(client, mock_api):
    resp = client.post(
        "/auth/check-user-providers",
        json={},
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_check_user_providers_backend_failure(client, mock_api):
    mock_api.post.return_value = _fail(500)
    resp = client.post(
        "/auth/check-user-providers",
        json={"email": "user@example.com"},
        content_type="application/json",
    )
    assert resp.status_code == 500


# ─── /auth/add-password ───────────────────────────────────────────────────────

def test_add_password_success(client, mock_api):
    mock_api.post.return_value = _ok({"custom_token": "ctoken"})
    resp = client.post(
        "/auth/add-password",
        json={"email": "u@example.com", "password": "pass1234", "verification_token": "vtok"},  # pragma: allowlist secret
        content_type="application/json",
    )
    assert resp.status_code == 200


def test_add_password_missing_fields(client, mock_api):
    resp = client.post(
        "/auth/add-password",
        json={"email": "u@example.com"},
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_add_password_backend_failure(client, mock_api):
    mock_api.post.return_value = _fail(400, {"detail": "Password already set"})
    resp = client.post(
        "/auth/add-password",
        json={"email": "u@example.com", "password": "pass1234", "verification_token": "vtok"},  # pragma: allowlist secret
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


# ─── /auth/check-phone-availability ──────────────────────────────────────────

def test_check_phone_availability_success(client, mock_api):
    mock_api.post.return_value = _ok({"available": True})
    resp = client.post(
        "/auth/check-phone-availability",
        json={"phone": "+911234567890"},
        content_type="application/json",
    )
    assert resp.status_code == 200
    assert resp.get_json()["available"] is True


def test_check_phone_availability_missing(client, mock_api):
    resp = client.post(
        "/auth/check-phone-availability",
        json={},
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_check_phone_availability_backend_failure(client, mock_api):
    mock_api.post.return_value = _fail(500)
    resp = client.post(
        "/auth/check-phone-availability",
        json={"phone": "+911234567890"},
        content_type="application/json",
    )
    assert resp.status_code == 500


# ─── /users/me/profile ────────────────────────────────────────────────────────

def test_get_user_profile_no_token(client, mock_api):
    resp = client.get("/users/me/profile")
    assert resp.status_code == 302


def test_get_user_profile_success(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _ok({"id": "u1", "full_name": "Test"})
    resp = client.get("/users/me/profile")
    assert resp.status_code == 200
    assert resp.get_json()["full_name"] == "Test"


def test_get_user_profile_api_failure(auth_client):
    client, mock_api = auth_client
    mock_api.get.return_value = _fail(404)
    resp = client.get("/users/me/profile")
    assert resp.status_code == 404


# ─── /users/me/phone ──────────────────────────────────────────────────────────

def test_update_user_phone_no_token(client, mock_api):
    resp = client.put(
        "/users/me/phone",
        json={"phone": "+911234567890"},
        content_type="application/json",
    )
    assert resp.status_code == 401


def test_update_user_phone_missing(auth_client):
    client, _ = auth_client
    resp = client.put(
        "/users/me/phone",
        json={},
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_update_user_phone_success(auth_client):
    client, mock_api = auth_client
    mock_api.put.return_value = _ok({"phone": "+911234567890"})
    resp = client.put(
        "/users/me/phone",
        json={"phone": "+911234567890"},
        content_type="application/json",
    )
    assert resp.status_code == 200


def test_update_user_phone_backend_failure(auth_client):
    client, mock_api = auth_client
    mock_api.put.return_value = _fail(400, {"detail": "Invalid phone"})
    resp = client.put(
        "/users/me/phone",
        json={"phone": "bad"},
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


# ─── /users/me/send-phone-otp ─────────────────────────────────────────────────

def test_send_phone_otp_no_token(client, mock_api):
    resp = client.post("/users/me/send-phone-otp")
    assert resp.status_code == 401


def test_send_phone_otp_success(auth_client):
    client, mock_api = auth_client
    mock_api.post.return_value = _ok({"message": "OTP sent"})
    resp = client.post("/users/me/send-phone-otp")
    assert resp.status_code == 200


def test_send_phone_otp_backend_failure(auth_client):
    client, mock_api = auth_client
    mock_api.post.return_value = _fail(502, {"detail": "Failed to send OTP"})
    resp = client.post("/users/me/send-phone-otp")
    assert resp.status_code == 502
    assert "error" in resp.get_json()


# ─── /users/me/verify-phone-otp ───────────────────────────────────────────────

def test_verify_phone_otp_no_token(client, mock_api):
    resp = client.post(
        "/users/me/verify-phone-otp",
        json={"otp": "123456"},
        content_type="application/json",
    )
    assert resp.status_code == 401


def test_verify_phone_otp_missing(auth_client):
    client, _ = auth_client
    resp = client.post(
        "/users/me/verify-phone-otp",
        json={},
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_verify_phone_otp_success(auth_client):
    client, mock_api = auth_client
    mock_api.post.return_value = _ok({"verified": True})
    resp = client.post(
        "/users/me/verify-phone-otp",
        json={"otp": "123456"},
        content_type="application/json",
    )
    assert resp.status_code == 200


def test_verify_phone_otp_backend_failure(auth_client):
    client, mock_api = auth_client
    mock_api.post.return_value = _fail(400, {"detail": "Invalid OTP"})
    resp = client.post(
        "/users/me/verify-phone-otp",
        json={"otp": "000000"},
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert "error" in resp.get_json()


# ─── /users/me/set-password ───────────────────────────────────────────────────

def test_set_password_no_token(client, mock_api):
    resp = client.post(
        "/users/me/set-password",
        json={"new_password": "pass1234"},  # pragma: allowlist secret
        content_type="application/json",
    )
    assert resp.status_code == 401


def test_set_password_too_short(auth_client):
    client, _ = auth_client
    resp = client.post(
        "/users/me/set-password",
        json={"new_password": "short"},  # pragma: allowlist secret
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_set_password_success(auth_client):
    client, mock_api = auth_client
    mock_api.post.return_value = _ok({"message": "Password set"})
    resp = client.post(
        "/users/me/set-password",
        json={"new_password": "newpass123"},  # pragma: allowlist secret
        content_type="application/json",
    )
    assert resp.status_code == 200


# ─── /users/me/change-password ────────────────────────────────────────────────

def test_change_password_no_token(client, mock_api):
    resp = client.post(
        "/users/me/change-password",
        json={"new_password": "pass1234"},  # pragma: allowlist secret
        content_type="application/json",
    )
    assert resp.status_code == 401


def test_change_password_missing(auth_client):
    client, _ = auth_client
    resp = client.post(
        "/users/me/change-password",
        json={},
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_change_password_too_short(auth_client):
    client, _ = auth_client
    resp = client.post(
        "/users/me/change-password",
        json={"new_password": "short"},  # pragma: allowlist secret
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_change_password_success(auth_client):
    client, mock_api = auth_client
    mock_api.post.return_value = _ok({"message": "Password changed"})
    resp = client.post(
        "/users/me/change-password",
        json={"new_password": "newpass123"},  # pragma: allowlist secret
        content_type="application/json",
    )
    assert resp.status_code == 200


# ─── /users/me/link-email-password ────────────────────────────────────────────

def test_link_email_password_no_token(client, mock_api):
    resp = client.post(
        "/users/me/link-email-password",
        json={"email": "u@example.com", "password": "pass1234"},  # pragma: allowlist secret
        content_type="application/json",
    )
    assert resp.status_code == 401


def test_link_email_password_missing(auth_client):
    client, _ = auth_client
    resp = client.post(
        "/users/me/link-email-password",
        json={"email": "u@example.com"},
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_link_email_password_too_short(auth_client):
    client, _ = auth_client
    resp = client.post(
        "/users/me/link-email-password",
        json={"email": "u@example.com", "password": "short"},  # pragma: allowlist secret
        content_type="application/json",
    )
    assert resp.status_code == 400


def test_link_email_password_success(auth_client):
    client, mock_api = auth_client
    mock_api.post.return_value = _ok({"message": "Linked"})
    resp = client.post(
        "/users/me/link-email-password",
        json={"email": "u@example.com", "password": "pass1234"},  # pragma: allowlist secret
        content_type="application/json",
    )
    assert resp.status_code == 200


# ─── token refresh path (_try_with_refresh) ───────────────────────────────────

def test_try_refresh_on_401(app, mock_api):
    """When API returns 401, token refresh is attempted and request retried."""
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess["token"] = "expired-token"
            sess["refresh_token"] = "valid-refresh"

        expired_resp = MagicMock()
        expired_resp.status_code = 401
        expired_resp.ok = False

        fresh_resp = MagicMock()
        fresh_resp.status_code = 200
        fresh_resp.ok = True
        fresh_resp.json.return_value = {"id": "u1", "full_name": "Test"}

        mock_api.get.side_effect = [expired_resp, fresh_resp]
        mock_api.post.return_value = _ok({"access_token": "new-token", "refresh_token": "new-refresh"})

        resp = c.get("/users/me/profile")
        assert resp.status_code == 200
