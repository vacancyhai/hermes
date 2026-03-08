"""
Unit tests for app/utils/api_client.py

All HTTP calls are mocked via unittest.mock.patch so no real server is needed.
Each test runs inside a Flask app context to allow current_app.config access.
"""
import pytest
from unittest.mock import MagicMock, patch

from app.utils.api_client import APIClient, APIError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok_response(data: dict) -> MagicMock:
    """Build a mock requests.Response that looks like a successful backend reply."""
    resp = MagicMock()
    resp.ok = True
    resp.status_code = 200
    resp.json.return_value = {"status": "success", "data": data}
    return resp


def _error_response(status_code: int, code: str, message: str) -> MagicMock:
    """Build a mock requests.Response that looks like a backend error."""
    resp = MagicMock()
    resp.ok = False
    resp.status_code = status_code
    resp.json.return_value = {
        "status": "error",
        "error": {"code": code, "message": message, "details": []},
    }
    return resp


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def api(app_ctx):
    """APIClient instance inside an active app context."""
    return APIClient()


# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------

class TestLogin:
    def test_calls_correct_url(self, api, app_ctx):
        with patch("requests.post") as mock_post:
            mock_post.return_value = _ok_response({"access_token": "tok", "refresh_token": "ref"})
            api.login("u@e.com", "pw")
            url = mock_post.call_args[0][0]
            assert url.endswith("/auth/login")

    def test_sends_email_and_password(self, api, app_ctx):
        with patch("requests.post") as mock_post:
            mock_post.return_value = _ok_response({"access_token": "tok", "refresh_token": "ref"})
            api.login("u@e.com", "secret")
            payload = mock_post.call_args[1]["json"]
            assert payload["email"] == "u@e.com"
            assert payload["password"] == "secret"

    def test_returns_data_dict(self, api, app_ctx):
        with patch("requests.post") as mock_post:
            mock_post.return_value = _ok_response({"access_token": "tok", "refresh_token": "ref"})
            result = api.login("u@e.com", "pw")
            assert result["access_token"] == "tok"


# ---------------------------------------------------------------------------
# register
# ---------------------------------------------------------------------------

class TestRegister:
    def test_calls_correct_url(self, api, app_ctx):
        with patch("requests.post") as mock_post:
            mock_post.return_value = _ok_response(
                {"user": {"id": "1"}, "access_token": "t", "refresh_token": "r"}
            )
            api.register("Bob", "b@e.com", "pw")
            url = mock_post.call_args[0][0]
            assert url.endswith("/auth/register")

    def test_sends_all_fields(self, api, app_ctx):
        with patch("requests.post") as mock_post:
            mock_post.return_value = _ok_response(
                {"user": {"id": "1"}, "access_token": "t", "refresh_token": "r"}
            )
            api.register("Bob", "b@e.com", "pass123")
            payload = mock_post.call_args[1]["json"]
            assert payload["full_name"] == "Bob"
            assert payload["email"] == "b@e.com"
            assert payload["password"] == "pass123"


# ---------------------------------------------------------------------------
# logout
# ---------------------------------------------------------------------------

class TestLogout:
    def test_calls_correct_url_with_bearer_header(self, api, app_ctx):
        with patch("requests.post") as mock_post:
            mock_post.return_value = _ok_response({})
            api.logout("access_tok", "refresh_tok")
            url = mock_post.call_args[0][0]
            headers = mock_post.call_args[1]["headers"]
            assert url.endswith("/auth/logout")
            assert headers["Authorization"] == "Bearer access_tok"


# ---------------------------------------------------------------------------
# refresh_tokens
# ---------------------------------------------------------------------------

class TestRefreshTokens:
    def test_sends_refresh_token_as_bearer(self, api, app_ctx):
        with patch("requests.post") as mock_post:
            mock_post.return_value = _ok_response({"access_token": "new_acc", "refresh_token": "new_ref"})
            result = api.refresh_tokens("old_refresh")
            headers = mock_post.call_args[1]["headers"]
            assert headers["Authorization"] == "Bearer old_refresh"
            assert result["access_token"] == "new_acc"


# ---------------------------------------------------------------------------
# forgot_password
# ---------------------------------------------------------------------------

class TestForgotPassword:
    def test_calls_correct_url_with_email(self, api, app_ctx):
        with patch("requests.post") as mock_post:
            mock_post.return_value = _ok_response({})
            api.forgot_password("u@e.com")
            url = mock_post.call_args[0][0]
            payload = mock_post.call_args[1]["json"]
            assert url.endswith("/auth/forgot-password")
            assert payload["email"] == "u@e.com"


# ---------------------------------------------------------------------------
# reset_password
# ---------------------------------------------------------------------------

class TestResetPassword:
    def test_calls_correct_url_with_token_and_password(self, api, app_ctx):
        with patch("requests.post") as mock_post:
            mock_post.return_value = _ok_response({})
            api.reset_password("reset-tok-123", "newpass")
            url = mock_post.call_args[0][0]
            payload = mock_post.call_args[1]["json"]
            assert url.endswith("/auth/reset-password")
            assert payload["token"] == "reset-tok-123"
            assert payload["new_password"] == "newpass"


# ---------------------------------------------------------------------------
# _handle_response — error paths
# ---------------------------------------------------------------------------

class TestHandleResponse:
    def test_raises_api_error_on_401(self, api, app_ctx):
        with patch("requests.post") as mock_post:
            mock_post.return_value = _error_response(401, "UNAUTHORIZED", "Invalid credentials.")
            with pytest.raises(APIError) as exc_info:
                api.login("x@y.com", "bad")
            err = exc_info.value
            assert err.status_code == 401
            assert err.code == "UNAUTHORIZED"
            assert "Invalid credentials" in err.message

    def test_raises_api_error_on_422(self, api, app_ctx):
        with patch("requests.post") as mock_post:
            mock_post.return_value = _error_response(422, "VALIDATION_ERROR", "Email is invalid.")
            with pytest.raises(APIError) as exc_info:
                api.register("X", "bad", "pw")
            assert exc_info.value.status_code == 422

    def test_raises_on_invalid_json_body(self, api, app_ctx):
        with patch("requests.post") as mock_post:
            resp = MagicMock()
            resp.ok = False
            resp.status_code = 500
            resp.json.side_effect = ValueError("No JSON")
            mock_post.return_value = resp
            with pytest.raises(APIError) as exc_info:
                api.login("x@y.com", "pw")
            assert exc_info.value.code == "INVALID_RESPONSE"

    def test_connection_error_raises_503(self, api, app_ctx):
        import requests as req_lib
        with patch("requests.post", side_effect=req_lib.exceptions.ConnectionError()):
            with pytest.raises(APIError) as exc_info:
                api.login("x@y.com", "pw")
            assert exc_info.value.status_code == 503
            assert exc_info.value.code == "SERVICE_UNAVAILABLE"

    def test_timeout_raises_504(self, api, app_ctx):
        import requests as req_lib
        with patch("requests.post", side_effect=req_lib.exceptions.Timeout()):
            with pytest.raises(APIError) as exc_info:
                api.login("x@y.com", "pw")
            assert exc_info.value.status_code == 504
            assert exc_info.value.code == "GATEWAY_TIMEOUT"
