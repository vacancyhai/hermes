"""
Integration tests for app/routes/jobs.py  (admin frontend)

Covers listing, creating, editing, and deleting job vacancies.
Role-based access control: list requires admin/operator login; create/edit
require admin or operator role; delete requires admin only.
APIClient calls and render_template are mocked.
"""
import pytest
from unittest.mock import patch

from app.utils.api_client import APIError

_PATCH_BASE = "app.routes.jobs"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _set_session(client, role="admin"):
    with client.session_transaction() as sess:
        sess["access_token"] = "test.admin.token"
        sess["user_id"] = "uid-admin-1"
        sess["role"] = role
        sess["email"] = "admin@example.com"


_SAMPLE_JOB = {
    "id": "job-1",
    "job_title": "Junior Clerk",
    "slug": "junior-clerk-1",
    "status": "active",
    "organization": "Test Dept",
    "job_type": "latest_job",
}
_SAMPLE_META = {"page": 1, "pages": 2, "total": 30, "per_page": 20}


# ---------------------------------------------------------------------------
# GET /jobs/  — list
# ---------------------------------------------------------------------------

class TestListJobs:
    def test_unauthenticated_redirects_to_login(self, client):
        resp = client.get("/jobs/", follow_redirects=False)
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers["Location"]

    def test_admin_returns_200(self, client):
        _set_session(client, role="admin")
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            mock_api.get_jobs.return_value = {"jobs": [_SAMPLE_JOB], "meta": _SAMPLE_META}
            resp = client.get("/jobs/")
        assert resp.status_code == 200

    def test_operator_returns_200(self, client):
        _set_session(client, role="operator")
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            mock_api.get_jobs.return_value = {"jobs": [], "meta": {}}
            resp = client.get("/jobs/")
        assert resp.status_code == 200

    def test_correct_template_used(self, client):
        _set_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            mock_api.get_jobs.return_value = {"jobs": [], "meta": {}}
            client.get("/jobs/")
        assert mock_rt.call_args[0][0] == "pages/jobs/list.html"

    def test_api_error_renders_empty_jobs(self, client):
        _set_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            mock_api.get_jobs.side_effect = APIError(503, "UNAVAILABLE", "Down")
            resp = client.get("/jobs/")
        assert resp.status_code == 200
        _, kw = mock_rt.call_args
        assert kw["jobs"] == []

    def test_filter_params_forwarded_to_api(self, client):
        _set_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            mock_api.get_jobs.return_value = {"jobs": [], "meta": {}}
            client.get("/jobs/?q=police&status=active&type=latest_job")
        kw = mock_api.get_jobs.call_args[1]
        assert kw.get("q") == "police"
        assert kw.get("status") == "active"


# ---------------------------------------------------------------------------
# GET /jobs/create
# ---------------------------------------------------------------------------

class TestCreateJobGet:
    def test_unauthenticated_redirects_to_login(self, client):
        resp = client.get("/jobs/create", follow_redirects=False)
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers["Location"]

    def test_plain_user_role_forbidden(self, client):
        # No plain-user sessions expected in admin app; simulate stale session
        with client.session_transaction() as sess:
            sess["access_token"] = "tok"
            sess["role"] = "user"
            sess["user_id"] = "uid-1"
        resp = client.get("/jobs/create", follow_redirects=False)
        assert resp.status_code == 302  # redirected by login_required role check

    def test_admin_returns_200(self, client):
        _set_session(client, role="admin")
        with patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            resp = client.get("/jobs/create")
        assert resp.status_code == 200

    def test_operator_returns_200(self, client):
        _set_session(client, role="operator")
        with patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            resp = client.get("/jobs/create")
        assert resp.status_code == 200

    def test_correct_template_used(self, client):
        _set_session(client)
        with patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            client.get("/jobs/create")
        assert mock_rt.call_args[0][0] == "pages/jobs/create.html"


# ---------------------------------------------------------------------------
# POST /jobs/create
# ---------------------------------------------------------------------------

class TestCreateJobPost:
    def test_successful_create_redirects_to_list(self, client):
        _set_session(client, role="admin")
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.create_job.return_value = {"job": _SAMPLE_JOB}
            resp = client.post(
                "/jobs/create",
                data={"job_title": "Clerk", "organization": "Dept", "job_type": "latest_job"},
                follow_redirects=False,
            )
        assert resp.status_code == 302
        assert "/jobs/" in resp.headers["Location"]

    def test_api_error_re_renders_create_form(self, client):
        _set_session(client, role="admin")
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            mock_api.create_job.side_effect = APIError(422, "VALIDATION_ERROR", "Invalid")
            resp = client.post(
                "/jobs/create",
                data={"job_title": "Clerk"},
            )
        assert resp.status_code == 200
        assert mock_rt.call_args[0][0] == "pages/jobs/create.html"

    def test_create_job_called_with_payload(self, client):
        _set_session(client, role="operator")
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.create_job.return_value = {"job": _SAMPLE_JOB}
            client.post(
                "/jobs/create",
                data={"job_title": "Constable", "organization": "Police"},
            )
        _, payload = mock_api.create_job.call_args[0][0], mock_api.create_job.call_args[0][1]
        assert payload.get("job_title") == "Constable"


# ---------------------------------------------------------------------------
# GET /jobs/<slug>/edit
# ---------------------------------------------------------------------------

class TestEditJobGet:
    def test_unauthenticated_redirects_to_login(self, client):
        resp = client.get("/jobs/junior-clerk-1/edit", follow_redirects=False)
        assert resp.status_code == 302

    def test_admin_returns_200(self, client):
        _set_session(client, role="admin")
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            mock_api.get_job.return_value = {"job": _SAMPLE_JOB}
            resp = client.get("/jobs/junior-clerk-1/edit")
        assert resp.status_code == 200

    def test_correct_template_used(self, client):
        _set_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            mock_api.get_job.return_value = {"job": _SAMPLE_JOB}
            client.get("/jobs/junior-clerk-1/edit")
        assert mock_rt.call_args[0][0] == "pages/jobs/edit.html"

    def test_api_error_redirects_to_list(self, client):
        _set_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.get_job.side_effect = APIError(404, "JOB_NOT_FOUND", "Not found")
            resp = client.get("/jobs/no-such/edit", follow_redirects=False)
        assert resp.status_code == 302
        assert "/jobs/" in resp.headers["Location"]


# ---------------------------------------------------------------------------
# POST /jobs/<slug>/edit
# ---------------------------------------------------------------------------

class TestEditJobPost:
    def test_successful_edit_redirects_to_list(self, client):
        _set_session(client, role="admin")
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.update_job.return_value = {"job": _SAMPLE_JOB}
            resp = client.post(
                "/jobs/junior-clerk-1/edit",
                data={"job_id": "job-1", "job_title": "Senior Clerk", "organization": "Dept"},
                follow_redirects=False,
            )
        assert resp.status_code == 302
        assert "/jobs/" in resp.headers["Location"]

    def test_api_error_redirects_to_edit(self, client):
        _set_session(client, role="admin")
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.update_job.side_effect = APIError(422, "VALIDATION_ERROR", "Invalid")
            resp = client.post(
                "/jobs/junior-clerk-1/edit",
                data={"job_id": "job-1", "job_title": "Clerk"},
                follow_redirects=False,
            )
        assert resp.status_code == 302
        assert "junior-clerk-1/edit" in resp.headers["Location"]


# ---------------------------------------------------------------------------
# POST /jobs/<job_id>/delete
# ---------------------------------------------------------------------------

class TestDeleteJob:
    def test_unauthenticated_redirects_to_login(self, client):
        resp = client.post("/jobs/job-1/delete", follow_redirects=False)
        assert resp.status_code == 302

    def test_operator_cannot_delete(self, client):
        _set_session(client, role="operator")
        resp = client.post("/jobs/job-1/delete", follow_redirects=False)
        assert resp.status_code == 302
        # Redirected to dashboard (role check), NOT to /jobs/
        assert "/jobs/" not in resp.headers.get("Location", "")

    def test_admin_can_delete(self, client):
        _set_session(client, role="admin")
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.delete_job.return_value = {}
            resp = client.post("/jobs/job-1/delete", follow_redirects=False)
        assert resp.status_code == 302
        assert "/jobs/" in resp.headers["Location"]

    def test_delete_called_with_correct_job_id(self, client):
        _set_session(client, role="admin")
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.delete_job.return_value = {}
            client.post("/jobs/job-abc/delete")
        args = mock_api.delete_job.call_args[0]
        assert "job-abc" in args

    def test_api_error_redirects_to_list(self, client):
        _set_session(client, role="admin")
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.delete_job.side_effect = APIError(404, "JOB_NOT_FOUND", "Not found")
            resp = client.post("/jobs/job-1/delete", follow_redirects=False)
        assert resp.status_code == 302
        assert "/jobs/" in resp.headers["Location"]
