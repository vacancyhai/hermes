"""
Unit tests for app/utils/api_client.py  (admin frontend)

Admin APIClient only exposes login, logout, and refresh_tokens — no register.
"""
import pytest
from unittest.mock import MagicMock, patch

from app.utils.api_client import APIClient, APIError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok_response(data: dict) -> MagicMock:
    resp = MagicMock()
    resp.ok = True
    resp.status_code = 200
    resp.json.return_value = {"status": "success", "data": data}
    return resp


def _error_response(status_code: int, code: str, message: str) -> MagicMock:
    resp = MagicMock()
    resp.ok = False
    resp.status_code = status_code
    resp.json.return_value = {
        "status": "error",
        "error": {"code": code, "message": message, "details": []},
    }
    return resp


@pytest.fixture
def api(app_ctx):
    return APIClient()


# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------

class TestLogin:
    def test_calls_correct_url(self, api):
        with patch("requests.post") as mock_post:
            mock_post.return_value = _ok_response({"access_token": "tok", "refresh_token": "ref"})
            api.login("admin@e.com", "pw")
            assert mock_post.call_args[0][0].endswith("/auth/login")

    def test_sends_credentials(self, api):
        with patch("requests.post") as mock_post:
            mock_post.return_value = _ok_response({"access_token": "tok", "refresh_token": "ref"})
            api.login("admin@e.com", "secret")
            payload = mock_post.call_args[1]["json"]
            assert payload["email"] == "admin@e.com"
            assert payload["password"] == "secret"

    def test_returns_data_dict(self, api):
        with patch("requests.post") as mock_post:
            mock_post.return_value = _ok_response({"access_token": "t", "refresh_token": "r"})
            result = api.login("admin@e.com", "pw")
            assert result["access_token"] == "t"

    def test_raises_on_invalid_credentials(self, api):
        with patch("requests.post") as mock_post:
            mock_post.return_value = _error_response(401, "UNAUTHORIZED", "Bad password.")
            with pytest.raises(APIError) as exc_info:
                api.login("x@y.com", "bad")
            assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# logout
# ---------------------------------------------------------------------------

class TestLogout:
    def test_sends_bearer_token(self, api):
        with patch("requests.post") as mock_post:
            mock_post.return_value = _ok_response({})
            api.logout("access_tok", "refresh_tok")
            headers = mock_post.call_args[1]["headers"]
            assert headers["Authorization"] == "Bearer access_tok"
            assert mock_post.call_args[0][0].endswith("/auth/logout")


# ---------------------------------------------------------------------------
# refresh_tokens
# ---------------------------------------------------------------------------

class TestRefreshTokens:
    def test_sends_refresh_as_bearer(self, api):
        with patch("requests.post") as mock_post:
            mock_post.return_value = _ok_response({"access_token": "new_a", "refresh_token": "new_r"})
            result = api.refresh_tokens("old_refresh")
            headers = mock_post.call_args[1]["headers"]
            assert headers["Authorization"] == "Bearer old_refresh"
            assert result["access_token"] == "new_a"


# ---------------------------------------------------------------------------
# Error / transport failures
# ---------------------------------------------------------------------------

class TestErrors:
    def test_connection_error_raises_503(self, api):
        import requests as req_lib
        with patch("requests.post", side_effect=req_lib.exceptions.ConnectionError()):
            with pytest.raises(APIError) as exc_info:
                api.login("x@y.com", "pw")
            assert exc_info.value.status_code == 503

    def test_timeout_raises_504(self, api):
        import requests as req_lib
        with patch("requests.post", side_effect=req_lib.exceptions.Timeout()):
            with pytest.raises(APIError) as exc_info:
                api.login("x@y.com", "pw")
            assert exc_info.value.status_code == 504

    def test_invalid_json_raises_api_error(self, api):
        resp = MagicMock()
        resp.ok = False
        resp.status_code = 500
        resp.json.side_effect = ValueError("No JSON")
        with patch("requests.post", return_value=resp):
            with pytest.raises(APIError) as exc_info:
                api.login("x@y.com", "pw")
            assert exc_info.value.code == "INVALID_RESPONSE"
