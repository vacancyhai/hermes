"""
Integration tests for app/routes/users.py  (admin frontend)

User management requires admin role only (not operator).
APIClient calls and render_template are mocked.
"""
import pytest
from unittest.mock import patch

from app.utils.api_client import APIError

_PATCH_BASE = "app.routes.users"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _set_session(client, role="admin"):
    with client.session_transaction() as sess:
        sess["access_token"] = "test.admin.token"
        sess["user_id"] = "uid-admin-1"
        sess["role"] = role
        sess["email"] = "admin@example.com"


_SAMPLE_USERS = [
    {"id": "u1", "email": "alice@example.com", "role": "user", "status": "active"},
    {"id": "u2", "email": "bob@example.com", "role": "user", "status": "suspended"},
]
_SAMPLE_META = {"page": 1, "pages": 3, "total": 50, "per_page": 20}


# ---------------------------------------------------------------------------
# GET /users/  — list
# ---------------------------------------------------------------------------

class TestListUsers:
    def test_unauthenticated_redirects_to_login(self, client):
        resp = client.get("/users/", follow_redirects=False)
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers["Location"]

    def test_operator_access_denied(self, client):
        _set_session(client, role="operator")
        resp = client.get("/users/", follow_redirects=False)
        assert resp.status_code == 302
        # Redirected to dashboard (not login)
        location = resp.headers.get("Location", "")
        assert "/auth/login" not in location

    def test_admin_returns_200(self, client):
        _set_session(client, role="admin")
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            mock_api.get_users.return_value = {"users": _SAMPLE_USERS, "meta": _SAMPLE_META}
            resp = client.get("/users/")
        assert resp.status_code == 200

    def test_correct_template_used(self, client):
        _set_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            mock_api.get_users.return_value = {"users": [], "meta": {}}
            client.get("/users/")
        assert mock_rt.call_args[0][0] == "pages/users/list.html"

    def test_passes_users_and_meta_to_template(self, client):
        _set_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            mock_api.get_users.return_value = {"users": _SAMPLE_USERS, "meta": _SAMPLE_META}
            client.get("/users/")
        _, kw = mock_rt.call_args
        assert kw["users"] == _SAMPLE_USERS
        assert kw["meta"] == _SAMPLE_META

    def test_api_error_renders_empty_users(self, client):
        _set_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            mock_api.get_users.side_effect = APIError(503, "UNAVAILABLE", "Down")
            resp = client.get("/users/")
        assert resp.status_code == 200
        _, kw = mock_rt.call_args
        assert kw["users"] == []

    def test_filter_params_forwarded_to_api(self, client):
        _set_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            mock_api.get_users.return_value = {"users": [], "meta": {}}
            client.get("/users/?q=alice&status=active&role=user")
        kw = mock_api.get_users.call_args[1]
        assert kw.get("q") == "alice"
        assert kw.get("status") == "active"
        assert kw.get("role") == "user"


# ---------------------------------------------------------------------------
# POST /users/<user_id>/status
# ---------------------------------------------------------------------------

class TestUpdateStatus:
    def test_unauthenticated_redirects_to_login(self, client):
        resp = client.post("/users/u1/status", data={"status": "active"}, follow_redirects=False)
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers["Location"]

    def test_operator_access_denied(self, client):
        _set_session(client, role="operator")
        resp = client.post(
            "/users/u1/status", data={"status": "active"}, follow_redirects=False
        )
        assert resp.status_code == 302

    def test_valid_status_calls_api(self, client):
        _set_session(client, role="admin")
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.update_user_status.return_value = {}
            client.post("/users/u1/status", data={"status": "suspended"})
        mock_api.update_user_status.assert_called_once()
        args = mock_api.update_user_status.call_args[0]
        assert "suspended" in args

    def test_valid_status_redirects_to_list(self, client):
        _set_session(client, role="admin")
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.update_user_status.return_value = {}
            resp = client.post(
                "/users/u1/status", data={"status": "active"}, follow_redirects=False
            )
        assert resp.status_code == 302
        assert "/users/" in resp.headers["Location"]

    def test_invalid_status_does_not_call_api(self, client):
        _set_session(client, role="admin")
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            resp = client.post(
                "/users/u1/status", data={"status": "deleted"}, follow_redirects=False
            )
        mock_api.update_user_status.assert_not_called()
        assert resp.status_code == 302

    def test_each_valid_status_accepted(self, client):
        for status in ("active", "suspended", "banned"):
            _set_session(client, role="admin")
            with patch(f"{_PATCH_BASE}._api") as mock_api:
                mock_api.update_user_status.return_value = {}
                resp = client.post(
                    "/users/u1/status", data={"status": status}, follow_redirects=False
                )
            assert resp.status_code == 302

    def test_api_error_redirects_to_list(self, client):
        _set_session(client, role="admin")
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.update_user_status.side_effect = APIError(
                404, "USER_NOT_FOUND", "Not found"
            )
            resp = client.post(
                "/users/u1/status", data={"status": "banned"}, follow_redirects=False
            )
        assert resp.status_code == 302
        assert "/users/" in resp.headers["Location"]
