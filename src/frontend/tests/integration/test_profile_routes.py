"""
Integration tests for app/routes/profile.py  (user frontend)

All profile routes require authentication; unauthenticated requests are
redirected to /auth/login.  APIClient calls and render_template are mocked.
"""
import pytest
from unittest.mock import patch

from app.utils.api_client import APIError

_PATCH_BASE = "app.routes.profile"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _set_auth_session(client):
    with client.session_transaction() as sess:
        sess["access_token"] = "test.access.token"
        sess["user_id"] = "uid-1"
        sess["role"] = "user"
        sess["email"] = "user@example.com"


_SAMPLE_USER = {
    "id": "uid-1",
    "email": "user@example.com",
    "full_name": "Test User",
    "role": "user",
}

_SAMPLE_PROFILE = {
    "date_of_birth": "1995-04-12",
    "gender": "male",
    "category": "general",
    "state": "Maharashtra",
    "city": "Pune",
    "highest_qualification": "graduation",
}


# ---------------------------------------------------------------------------
# GET /profile/
# ---------------------------------------------------------------------------

class TestProfileIndex:
    def test_unauthenticated_redirects_to_login(self, client):
        resp = client.get("/profile/", follow_redirects=False)
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers["Location"]

    def test_authenticated_returns_200(self, client):
        _set_auth_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            mock_api.get_profile.return_value = {
                "user": _SAMPLE_USER, "profile": _SAMPLE_PROFILE
            }
            resp = client.get("/profile/")
        assert resp.status_code == 200

    def test_correct_template_used(self, client):
        _set_auth_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            mock_api.get_profile.return_value = {"user": _SAMPLE_USER, "profile": _SAMPLE_PROFILE}
            client.get("/profile/")
        assert mock_rt.call_args[0][0] == "pages/profile/index.html"

    def test_passes_user_and_profile_to_template(self, client):
        _set_auth_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            mock_api.get_profile.return_value = {
                "user": _SAMPLE_USER, "profile": _SAMPLE_PROFILE
            }
            client.get("/profile/")
        _, kw = mock_rt.call_args
        assert kw["user"] == _SAMPLE_USER
        assert kw["profile"] == _SAMPLE_PROFILE

    def test_api_error_renders_with_empty_data(self, client):
        _set_auth_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            mock_api.get_profile.side_effect = APIError(500, "SERVER_ERROR", "Down")
            resp = client.get("/profile/")
        assert resp.status_code == 200
        _, kw = mock_rt.call_args
        assert kw["user"] == {}
        assert kw["profile"] == {}


# ---------------------------------------------------------------------------
# GET /profile/edit
# ---------------------------------------------------------------------------

class TestProfileEditGet:
    def test_unauthenticated_redirects_to_login(self, client):
        resp = client.get("/profile/edit", follow_redirects=False)
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers["Location"]

    def test_returns_200(self, client):
        _set_auth_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            mock_api.get_profile.return_value = {
                "user": _SAMPLE_USER, "profile": _SAMPLE_PROFILE
            }
            resp = client.get("/profile/edit")
        assert resp.status_code == 200

    def test_correct_template_used(self, client):
        _set_auth_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            mock_api.get_profile.return_value = {"user": _SAMPLE_USER, "profile": _SAMPLE_PROFILE}
            client.get("/profile/edit")
        assert mock_rt.call_args[0][0] == "pages/profile/edit.html"


# ---------------------------------------------------------------------------
# POST /profile/edit
# ---------------------------------------------------------------------------

class TestProfileEditPost:
    def test_unauthenticated_redirects_to_login(self, client):
        resp = client.post("/profile/edit", data={}, follow_redirects=False)
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers["Location"]

    def test_successful_update_redirects_to_profile(self, client):
        _set_auth_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.update_profile.return_value = {}
            resp = client.post(
                "/profile/edit",
                data={"full_name": "Updated Name", "city": "Mumbai"},
                follow_redirects=False,
            )
        assert resp.status_code == 302
        assert "/profile/" in resp.headers["Location"]

    def test_update_profile_called_with_payload(self, client):
        _set_auth_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.update_profile.return_value = {}
            client.post(
                "/profile/edit",
                data={"full_name": "Test Name", "city": "Mumbai"},
            )
        _, payload = mock_api.update_profile.call_args[0][0], mock_api.update_profile.call_args[0][1]
        assert payload.get("full_name") == "Test Name"
        assert payload.get("city") == "Mumbai"

    def test_blank_fields_not_included_in_payload(self, client):
        _set_auth_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.update_profile.return_value = {}
            client.post(
                "/profile/edit",
                data={"full_name": "Name", "city": ""},
            )
        _, payload = mock_api.update_profile.call_args[0][0], mock_api.update_profile.call_args[0][1]
        assert "city" not in payload

    def test_api_error_redirects_to_profile(self, client):
        _set_auth_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.update_profile.side_effect = APIError(400, "VALIDATION_ERROR", "Invalid data")
            resp = client.post("/profile/edit", data={"full_name": "Name"}, follow_redirects=False)
        assert resp.status_code == 302


# ---------------------------------------------------------------------------
# GET /profile/applications
# ---------------------------------------------------------------------------

class TestProfileApplications:
    def test_unauthenticated_redirects_to_login(self, client):
        resp = client.get("/profile/applications", follow_redirects=False)
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers["Location"]

    def test_returns_200(self, client):
        _set_auth_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            mock_api.get_applications.return_value = {"applications": [], "meta": {}}
            resp = client.get("/profile/applications")
        assert resp.status_code == 200

    def test_correct_template_used(self, client):
        _set_auth_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            mock_api.get_applications.return_value = {"applications": [], "meta": {}}
            client.get("/profile/applications")
        assert mock_rt.call_args[0][0] == "pages/profile/applications.html"

    def test_passes_applications_and_meta_to_template(self, client):
        _set_auth_session(client)
        apps = [{"id": "app-1", "job_id": "job-1", "status": "pending"}]
        meta = {"page": 1, "pages": 1, "total": 1}
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            mock_api.get_applications.return_value = {"applications": apps, "meta": meta}
            client.get("/profile/applications")
        _, kw = mock_rt.call_args
        assert kw["applications"] == apps
        assert kw["meta"] == meta

    def test_api_error_renders_empty(self, client):
        _set_auth_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            mock_api.get_applications.side_effect = APIError(500, "SERVER_ERROR", "Down")
            resp = client.get("/profile/applications")
        assert resp.status_code == 200
        _, kw = mock_rt.call_args
        assert kw["applications"] == []


# ---------------------------------------------------------------------------
# POST /profile/applications/<id>/withdraw
# ---------------------------------------------------------------------------

class TestWithdraw:
    def test_unauthenticated_redirects_to_login(self, client):
        resp = client.post("/profile/applications/app-1/withdraw", follow_redirects=False)
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers["Location"]

    def test_successful_withdraw_redirects_to_applications(self, client):
        _set_auth_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.withdraw_application.return_value = {}
            resp = client.post(
                "/profile/applications/app-1/withdraw", follow_redirects=False
            )
        assert resp.status_code == 302
        assert "/profile/applications" in resp.headers["Location"]

    def test_withdraw_called_with_correct_id(self, client):
        _set_auth_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.withdraw_application.return_value = {}
            client.post("/profile/applications/app-xyz/withdraw")
        args = mock_api.withdraw_application.call_args[0]
        assert "app-xyz" in args

    def test_api_error_redirects_to_applications(self, client):
        _set_auth_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.withdraw_application.side_effect = APIError(
                404, "APPLICATION_NOT_FOUND", "Not found"
            )
            resp = client.post(
                "/profile/applications/app-1/withdraw", follow_redirects=False
            )
        assert resp.status_code == 302
        assert "/profile/applications" in resp.headers["Location"]
