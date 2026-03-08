"""
Integration tests for app/routes/jobs.py  (user frontend)

APIClient calls and render_template are mocked; no real HTTP or templates needed.
"""
import pytest
from unittest.mock import patch

from app.utils.api_client import APIError

_PATCH_BASE = "app.routes.jobs"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _set_auth_session(client):
    """Put a minimal authenticated session in place for the test client."""
    with client.session_transaction() as sess:
        sess["access_token"] = "test.access.token"
        sess["user_id"] = "uid-1"
        sess["role"] = "user"
        sess["email"] = "user@example.com"


_SAMPLE_JOB = {
    "id": "job-1",
    "job_title": "Junior Clerk",
    "slug": "junior-clerk-1",
    "organization": "Test Dept",
    "job_type": "latest_job",
    "total_vacancies": 50,
    "salary_min": 25000,
    "salary_max": 35000,
}

_SAMPLE_META = {"page": 1, "pages": 2, "total": 20, "per_page": 12}


# ---------------------------------------------------------------------------
# GET /jobs/  — list
# ---------------------------------------------------------------------------

class TestListJobs:
    def test_returns_200(self, client):
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            mock_api.get_jobs.return_value = {"jobs": [], "meta": {}}
            resp = client.get("/jobs/")
        assert resp.status_code == 200

    def test_passes_jobs_and_meta_to_template(self, client):
        jobs = [_SAMPLE_JOB]
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            mock_api.get_jobs.return_value = {"jobs": jobs, "meta": _SAMPLE_META}
            client.get("/jobs/")
        _, kw = mock_rt.call_args
        assert kw["jobs"] == jobs
        assert kw["meta"] == _SAMPLE_META

    def test_correct_template_used(self, client):
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            mock_api.get_jobs.return_value = {"jobs": [], "meta": {}}
            client.get("/jobs/")
        assert mock_rt.call_args[0][0] == "pages/jobs/list.html"

    def test_api_error_renders_empty_jobs(self, client):
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            mock_api.get_jobs.side_effect = APIError(503, "UNAVAILABLE", "Service down")
            resp = client.get("/jobs/")
        assert resp.status_code == 200
        _, kw = mock_rt.call_args
        assert kw["jobs"] == []

    def test_query_params_forwarded_to_api(self, client):
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            mock_api.get_jobs.return_value = {"jobs": [], "meta": {}}
            client.get("/jobs/?q=police&type=latest_job&qualification=graduation")
        kw = mock_api.get_jobs.call_args[1]
        assert kw.get("q") == "police"
        assert kw.get("type") == "latest_job"
        assert kw.get("qualification") == "graduation"

    def test_page_param_forwarded(self, client):
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            mock_api.get_jobs.return_value = {"jobs": [], "meta": {}}
            client.get("/jobs/?page=3")
        kw = mock_api.get_jobs.call_args[1]
        assert kw.get("page") == 3


# ---------------------------------------------------------------------------
# GET /jobs/<slug>  — detail
# ---------------------------------------------------------------------------

class TestJobDetail:
    def test_returns_200(self, client):
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            mock_api.get_job.return_value = {"job": _SAMPLE_JOB}
            resp = client.get("/jobs/junior-clerk-1")
        assert resp.status_code == 200

    def test_correct_template_used(self, client):
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            mock_api.get_job.return_value = {"job": _SAMPLE_JOB}
            client.get("/jobs/junior-clerk-1")
        assert mock_rt.call_args[0][0] == "pages/jobs/detail.html"

    def test_returns_404_when_api_raises_404(self, client):
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            mock_api.get_job.side_effect = APIError(404, "JOB_NOT_FOUND", "Not found")
            resp = client.get("/jobs/no-such-slug")
        assert resp.status_code == 404

    def test_non_404_api_error_redirects_to_list(self, client):
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.get_job.side_effect = APIError(500, "SERVER_ERROR", "Oops")
            resp = client.get("/jobs/some-slug", follow_redirects=False)
        assert resp.status_code == 302
        assert "/jobs/" in resp.headers["Location"]

    def test_authenticated_detects_already_applied(self, client):
        _set_auth_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            mock_api.get_job.return_value = {"job": _SAMPLE_JOB}
            mock_api.get_applications.return_value = {
                "applications": [{"job_id": "job-1"}]
            }
            client.get("/jobs/junior-clerk-1")
        _, kw = mock_rt.call_args
        assert kw["already_applied"] is True

    def test_authenticated_not_applied_returns_false(self, client):
        _set_auth_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>") as mock_rt:
            mock_api.get_job.return_value = {"job": _SAMPLE_JOB}
            mock_api.get_applications.return_value = {"applications": []}
            client.get("/jobs/junior-clerk-1")
        _, kw = mock_rt.call_args
        assert kw["already_applied"] is False

    def test_unauthenticated_does_not_check_applications(self, client):
        with patch(f"{_PATCH_BASE}._api") as mock_api, \
             patch(f"{_PATCH_BASE}.render_template", return_value="<html/>"):
            mock_api.get_job.return_value = {"job": _SAMPLE_JOB}
            client.get("/jobs/junior-clerk-1")
        mock_api.get_applications.assert_not_called()


# ---------------------------------------------------------------------------
# POST /jobs/<job_id>/apply
# ---------------------------------------------------------------------------

class TestApply:
    def test_unauthenticated_redirects_to_login(self, client):
        resp = client.post("/jobs/job-1/apply", follow_redirects=False)
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers["Location"]

    def test_successful_apply_redirects_to_job_detail(self, client):
        _set_auth_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.apply_to_job.return_value = {}
            resp = client.post(
                "/jobs/job-1/apply",
                data={"slug": "junior-clerk-1"},
                follow_redirects=False,
            )
        assert resp.status_code == 302
        assert "junior-clerk-1" in resp.headers["Location"]

    def test_successful_apply_without_slug_redirects_to_list(self, client):
        _set_auth_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.apply_to_job.return_value = {}
            resp = client.post("/jobs/job-1/apply", data={}, follow_redirects=False)
        assert resp.status_code == 302
        assert "/jobs/" in resp.headers["Location"]

    def test_apply_calls_api_with_correct_job_id(self, client):
        _set_auth_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.apply_to_job.return_value = {}
            client.post("/jobs/job-abc/apply", data={})
        args = mock_api.apply_to_job.call_args[0]
        assert "job-abc" in args

    def test_api_error_redirects_with_flash(self, client):
        _set_auth_session(client)
        with patch(f"{_PATCH_BASE}._api") as mock_api:
            mock_api.apply_to_job.side_effect = APIError(
                409, "ALREADY_APPLIED", "Already applied"
            )
            resp = client.post("/jobs/job-1/apply", data={}, follow_redirects=False)
        assert resp.status_code == 302
