"""
Integration tests for app/routes/dashboard.py  (admin frontend)

All dashboard routes require admin or operator role.
APIClient calls and render_template are mocked.
"""
import pytest
from unittest.mock import patch

from app.utils.api_client import APIError

_PATCH_BASE = "app.routes.dashboard"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _set_admin_session(client, role="admin"):
    with client.session_transaction() as sess:
        sess["access_token"] = "test.admin.token"
        sess["user_id"] = "uid-admin-1"
        sess["role"] = role
        sess["email"] = "admin@example.com"


_SAMPLE_JOBS = [
    {"id": "j1", "job_title": "Clerk", "slug": "clerk-1", "status": "active"},
    {"id": "j2", "job_title": "Inspector", "slug": "inspector-1", "status": "active"},
]
_SAMPLE_USERS = [
    {"id": "u1", "email": "a@example.com", "role": "user", "status": "active"},
]
_JOBS_META = {"page": 1, "pages": 3, "total": 25, "per_page": 5}
_USERS_META = {"page": 1, "pages": 2, "total": 10, "per_page": 5}


# ---------------------------------------------------------------------------
# GET /dashboard/
# ---------------------------------------------------------------------------

class TestDashboardIndex:
    def test_unauthenticated_redirects_to_login(self, client):
        resp = client.get("/dashboard/", follow_redirects=False)
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers["Location"]

    def test_admin_returns_200(self, client):
        _set_admin_session(client, role="admin")
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            mock_api.get_jobs.return_value = {"jobs": _SAMPLE_JOBS, "meta": _JOBS_META}
            mock_api.get_users.return_value = {"users": _SAMPLE_USERS, "meta": _USERS_META}
            resp = client.get("/dashboard/")
        assert resp.status_code == 200

    def test_operator_returns_200(self, client):
        _set_admin_session(client, role="operator")
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            mock_api.get_jobs.return_value = {"jobs": [], "meta": {}}
            mock_api.get_users.return_value = {"users": [], "meta": {}}
            resp = client.get("/dashboard/")
        assert resp.status_code == 200

    def test_correct_template_used(self, client):
        _set_admin_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            mock_api.get_jobs.return_value = {"jobs": [], "meta": {}}
            mock_api.get_users.return_value = {"users": [], "meta": {}}
            client.get("/dashboard/")
        assert mock_rt.call_args[0][0] == "pages/dashboard/index.html"

    def test_passes_recent_jobs_and_users_to_template(self, client):
        _set_admin_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            mock_api.get_jobs.return_value = {"jobs": _SAMPLE_JOBS, "meta": _JOBS_META}
            mock_api.get_users.return_value = {"users": _SAMPLE_USERS, "meta": _USERS_META}
            client.get("/dashboard/")
        _, kw = mock_rt.call_args
        assert kw["recent_jobs"] == _SAMPLE_JOBS
        assert kw["recent_users"] == _SAMPLE_USERS
        assert kw["jobs_meta"] == _JOBS_META
        assert kw["users_meta"] == _USERS_META

    def test_jobs_api_error_renders_with_empty_jobs(self, client):
        _set_admin_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            mock_api.get_jobs.side_effect = APIError(503, "UNAVAILABLE", "Down")
            mock_api.get_users.return_value = {"users": _SAMPLE_USERS, "meta": _USERS_META}
            resp = client.get("/dashboard/")
        assert resp.status_code == 200
        _, kw = mock_rt.call_args
        assert kw["recent_jobs"] == []

    def test_users_api_error_renders_with_empty_users(self, client):
        _set_admin_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            mock_api.get_jobs.return_value = {"jobs": _SAMPLE_JOBS, "meta": _JOBS_META}
            mock_api.get_users.side_effect = APIError(503, "UNAVAILABLE", "Down")
            resp = client.get("/dashboard/")
        assert resp.status_code == 200
        _, kw = mock_rt.call_args
        assert kw["recent_users"] == []
