"""
Integration tests for app/routes/auth.py  (admin frontend)

Tests cover the role-based access control on top of standard auth flow:
  - Admin/operator login → session saved, redirect to dashboard
  - Plain user login → token blocklisted, access denied flash shown
  - Invalid credentials → form re-rendered with error
  - Logout → session cleared, redirect to login
"""
import pytest
from unittest.mock import patch, MagicMock

from app.utils.api_client import APIError

_PATCH_BASE = "app.routes.auth"


# ---------------------------------------------------------------------------
# GET /auth/login
# ---------------------------------------------------------------------------

class TestLoginGet:
    def test_returns_200(self, client):
        with patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            resp = client.get("/auth/login")
            assert resp.status_code == 200
            mock_rt.assert_called_once_with("auth/login.html")


# ---------------------------------------------------------------------------
# POST /auth/login — happy paths
# ---------------------------------------------------------------------------

class TestLoginPostSuccess:
    def test_admin_login_redirects_to_dashboard(self, client, fake_login_data):
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.login.return_value = fake_login_data
            resp = client.post(
                "/auth/login",
                data={"email": "admin@example.com", "password": "pw"},
                follow_redirects=False,
            )
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_operator_login_redirects_to_dashboard(self, client, fake_operator_data):
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.login.return_value = fake_operator_data
            resp = client.post(
                "/auth/login",
                data={"email": "op@example.com", "password": "pw"},
                follow_redirects=False,
            )
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["Location"]

    def test_successful_login_populates_session(self, client, fake_login_data):
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.login.return_value = fake_login_data
            client.post(
                "/auth/login",
                data={"email": "admin@example.com", "password": "pw"},
            )
        with client.session_transaction() as sess:
            assert sess.get("access_token") is not None
            assert sess.get("role") == "admin"


# ---------------------------------------------------------------------------
# POST /auth/login — role rejection (plain user)
# ---------------------------------------------------------------------------

class TestLoginPostUserRejected:
    def test_user_role_shows_access_denied(self, client, fake_user_data):
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            mock_api.login.return_value = fake_user_data
            resp = client.post(
                "/auth/login",
                data={"email": "user@example.com", "password": "pw"},
            )
            # Must blocklist the token
            mock_api.logout.assert_called_once()
        assert resp.status_code == 200  # re-renders form

    def test_user_role_does_not_save_session(self, client, fake_user_data):
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            mock_api.login.return_value = fake_user_data
            client.post(
                "/auth/login",
                data={"email": "user@example.com", "password": "pw"},
            )
        with client.session_transaction() as sess:
            assert "access_token" not in sess


# ---------------------------------------------------------------------------
# POST /auth/login — API / validation errors
# ---------------------------------------------------------------------------

class TestLoginPostErrors:
    def test_api_error_returns_200(self, client):
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            mock_api.login.side_effect = APIError(401, "UNAUTHORIZED", "Bad credentials.")
            resp = client.post(
                "/auth/login",
                data={"email": "a@a.com", "password": "bad"},
            )
        assert resp.status_code == 200

    def test_missing_email_no_api_call(self, client):
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            resp = client.post("/auth/login", data={"email": "", "password": "pw"})
            mock_api.login.assert_not_called()
        assert resp.status_code == 200

    def test_missing_password_no_api_call(self, client):
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            resp = client.post("/auth/login", data={"email": "a@a.com", "password": ""})
            mock_api.login.assert_not_called()
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------

class TestLogout:
    def _login(self, client, fake_login_data):
        with client.session_transaction() as sess:
            sess["access_token"] = fake_login_data["access_token"]
            sess["refresh_token"] = fake_login_data["refresh_token"]
            sess["user_id"] = "uid-admin-1"
            sess["email"] = "admin@example.com"
            sess["full_name"] = ""
            sess["role"] = "admin"

    def test_logout_redirects_to_login(self, client, fake_login_data):
        self._login(client, fake_login_data)
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.logout.return_value = None
            resp = client.post("/auth/logout", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/auth/login")

    def test_logout_clears_session(self, client, fake_login_data):
        self._login(client, fake_login_data)
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.logout.return_value = None
            client.post("/auth/logout")
        with client.session_transaction() as sess:
            assert "access_token" not in sess

    def test_logout_clears_session_even_if_api_errors(self, client, fake_login_data):
        self._login(client, fake_login_data)
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.logout.side_effect = APIError(500, "ERROR", "Server blew up.")
            client.post("/auth/logout")
        with client.session_transaction() as sess:
            assert "access_token" not in sess
