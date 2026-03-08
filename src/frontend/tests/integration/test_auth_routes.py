"""
Integration tests for app/routes/auth.py  (user frontend)

The Flask test client is used to exercise the full request/response cycle.
APIClient methods are mocked to avoid real HTTP calls to the backend.
render_template is also mocked so tests run even without HTML template files.
"""
import pytest
from unittest.mock import patch, MagicMock

from app.utils.api_client import APIError

# Patch target for the module-level _api instance in the auth routes
_PATCH_BASE = "app.routes.auth"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_jwt(payload: dict) -> str:
    import base64, json
    header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
    body = base64.urlsafe_b64encode(
        json.dumps(payload).encode()
    ).rstrip(b"=").decode()
    return f"{header}.{body}.fakesig"


def _login_api_data(role="user", email="u@example.com", user_id="uid-1"):
    token = _make_jwt({"sub": user_id, "role": role, "email": email})
    return {"access_token": token, "refresh_token": "refresh.tok"}


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
# POST /auth/login
# ---------------------------------------------------------------------------

class TestLoginPost:
    def test_successful_login_redirects(self, client, fake_login_data):
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.login.return_value = fake_login_data
            resp = client.post(
                "/auth/login",
                data={"email": "u@example.com", "password": "correct"},
                follow_redirects=False,
            )
        assert resp.status_code == 302
        assert "/auth/login" not in resp.headers["Location"]

    def test_successful_login_populates_session(self, client, fake_login_data):
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.login.return_value = fake_login_data
            with client.session_transaction() as pre:
                assert "access_token" not in pre  # nothing yet
            client.post(
                "/auth/login",
                data={"email": "u@example.com", "password": "correct"},
            )
        with client.session_transaction() as post_sess:
            assert post_sess.get("access_token") is not None
            assert post_sess.get("user_id") == "uid-123"

    def test_api_error_returns_200_with_flash(self, client):
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            mock_api.login.side_effect = APIError(401, "UNAUTHORIZED", "Bad credentials.")
            resp = client.post(
                "/auth/login",
                data={"email": "u@example.com", "password": "wrong"},
            )
        assert resp.status_code == 200

    def test_missing_email_shows_error_no_api_call(self, client):
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            resp = client.post(
                "/auth/login",
                data={"email": "", "password": "pw"},
            )
            mock_api.login.assert_not_called()
        assert resp.status_code == 200

    def test_missing_password_shows_error_no_api_call(self, client):
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            resp = client.post(
                "/auth/login",
                data={"email": "u@e.com", "password": ""},
            )
            mock_api.login.assert_not_called()
        assert resp.status_code == 200

    def test_next_param_used_for_redirect(self, client, fake_login_data):
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.login.return_value = fake_login_data
            resp = client.post(
                "/auth/login?next=/jobs",
                data={"email": "u@example.com", "password": "correct"},
                follow_redirects=False,
            )
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/jobs")

    def test_unsafe_next_param_ignored(self, client, fake_login_data):
        """next= pointing to an external domain should be ignored."""
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.login.return_value = fake_login_data
            resp = client.post(
                "/auth/login?next=http://evil.com",
                data={"email": "u@example.com", "password": "correct"},
                follow_redirects=False,
            )
        assert resp.status_code == 302
        assert "evil.com" not in resp.headers["Location"]


# ---------------------------------------------------------------------------
# GET /auth/register
# ---------------------------------------------------------------------------

class TestRegisterGet:
    def test_returns_200(self, client):
        with patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            resp = client.get("/auth/register")
            assert resp.status_code == 200
            mock_rt.assert_called_once_with("auth/register.html")


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------

class TestRegisterPost:
    def test_successful_register_redirects(self, client, fake_register_data):
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.register.return_value = fake_register_data
            resp = client.post(
                "/auth/register",
                data={
                    "full_name": "New User",
                    "email": "new@example.com",
                    "password": "pw123",
                    "confirm_password": "pw123",
                },
                follow_redirects=False,
            )
        assert resp.status_code == 302

    def test_password_mismatch_no_api_call(self, client):
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            resp = client.post(
                "/auth/register",
                data={
                    "full_name": "X",
                    "email": "x@e.com",
                    "password": "abc",
                    "confirm_password": "xyz",
                },
            )
            mock_api.register.assert_not_called()
        assert resp.status_code == 200

    def test_missing_field_no_api_call(self, client):
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            resp = client.post(
                "/auth/register",
                data={"full_name": "", "email": "x@e.com", "password": "pw", "confirm_password": "pw"},
            )
            mock_api.register.assert_not_called()
        assert resp.status_code == 200

    def test_api_error_returns_200(self, client):
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            mock_api.register.side_effect = APIError(409, "EMAIL_EXISTS", "Email already registered.")
            resp = client.post(
                "/auth/register",
                data={
                    "full_name": "X",
                    "email": "dup@e.com",
                    "password": "pw",
                    "confirm_password": "pw",
                },
            )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------

class TestLogout:
    def _login(self, client, fake_login_data):
        """Helper: log the client in by populating the session directly."""
        with client.session_transaction() as sess:
            sess["access_token"] = fake_login_data["access_token"]
            sess["refresh_token"] = fake_login_data["refresh_token"]
            sess["user_id"] = "uid-123"
            sess["email"] = "u@example.com"
            sess["full_name"] = ""
            sess["role"] = "user"

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

    def test_logout_clears_session_even_if_api_fails(self, client, fake_login_data):
        """Backend logout failure must not leave user logged in."""
        self._login(client, fake_login_data)
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.logout.side_effect = APIError(401, "UNAUTHORIZED", "Token expired.")
            client.post("/auth/logout")
        with client.session_transaction() as sess:
            assert "access_token" not in sess


# ---------------------------------------------------------------------------
# GET /auth/forgot-password
# ---------------------------------------------------------------------------

class TestForgotPasswordGet:
    def test_returns_200(self, client):
        with patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            resp = client.get("/auth/forgot-password")
            assert resp.status_code == 200
            mock_rt.assert_called_once_with("auth/forgot_password.html")


# ---------------------------------------------------------------------------
# POST /auth/forgot-password
# ---------------------------------------------------------------------------

class TestForgotPasswordPost:
    def test_shows_success_on_valid_email(self, client):
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            mock_api.forgot_password.return_value = {}
            resp = client.post("/auth/forgot-password", data={"email": "u@e.com"})
        assert resp.status_code == 200
        mock_api.forgot_password.assert_called_once_with("u@e.com")

    def test_missing_email_no_api_call(self, client):
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            resp = client.post("/auth/forgot-password", data={"email": ""})
            mock_api.forgot_password.assert_not_called()
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /auth/reset-password
# ---------------------------------------------------------------------------

class TestResetPasswordGet:
    def test_redirects_when_no_token(self, client):
        resp = client.get("/auth/reset-password", follow_redirects=False)
        assert resp.status_code == 302
        assert "forgot-password" in resp.headers["Location"]

    def test_returns_200_with_valid_token(self, client):
        with patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            resp = client.get("/auth/reset-password?token=abc123")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# POST /auth/reset-password
# ---------------------------------------------------------------------------

class TestResetPasswordPost:
    def test_successful_reset_redirects_to_login(self, client):
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.reset_password.return_value = {}
            resp = client.post(
                "/auth/reset-password",
                data={"token": "tok", "new_password": "newpw", "confirm_password": "newpw"},
                follow_redirects=False,
            )
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/auth/login")

    def test_passwords_mismatch_no_api_call(self, client):
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            resp = client.post(
                "/auth/reset-password",
                data={"token": "tok", "new_password": "a", "confirm_password": "b"},
            )
            mock_api.reset_password.assert_not_called()
        assert resp.status_code == 200

    def test_api_error_returns_200(self, client):
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            mock_api.reset_password.side_effect = APIError(400, "INVALID_TOKEN", "Token expired.")
            resp = client.post(
                "/auth/reset-password",
                data={"token": "bad", "new_password": "pw", "confirm_password": "pw"},
            )
        assert resp.status_code == 200
