"""
E2E tests: public job listing and detail endpoints via the backend API.

These tests only use unauthenticated requests because job listing / detail
are publicly accessible (no JWT required).
"""
import pytest
import requests


class TestJobListing:
    def test_list_jobs_returns_200(self, api_url, anon_session):
        resp = anon_session.get(f'{api_url}/jobs')
        assert resp.status_code == 200

    def test_list_jobs_response_structure(self, api_url, anon_session):
        resp = anon_session.get(f'{api_url}/jobs')
        assert resp.status_code == 200
        data = resp.json()
        # Expect a paginated wrapper
        assert 'items' in data or 'jobs' in data or isinstance(data, list), (
            f'Unexpected jobs response shape: {list(data.keys()) if isinstance(data, dict) else type(data)}'
        )

    def test_list_jobs_pagination_params(self, api_url, anon_session):
        resp = anon_session.get(f'{api_url}/jobs', params={'page': 1, 'per_page': 5})
        assert resp.status_code == 200

    def test_list_jobs_search_filter(self, api_url, anon_session):
        resp = anon_session.get(f'{api_url}/jobs', params={'q': 'engineer'})
        assert resp.status_code == 200

    def test_list_jobs_job_type_filter(self, api_url, anon_session):
        for job_type in ('central', 'state', 'psu', 'defence', 'teaching', 'other'):
            resp = anon_session.get(f'{api_url}/jobs', params={'job_type': job_type})
            assert resp.status_code == 200, (
                f'job_type={job_type!r} returned {resp.status_code}'
            )

    def test_list_jobs_invalid_page_returns_400_or_200(self, api_url, anon_session):
        # Some implementations return empty list, others return 400 — both acceptable
        resp = anon_session.get(f'{api_url}/jobs', params={'page': -1})
        assert resp.status_code in (200, 400)


class TestJobDetail:
    @pytest.fixture(scope='class')
    def first_job_id(self, api_url):
        """Fetch the first available job ID for detail tests. Skip if none."""
        resp = requests.get(f'{api_url}/jobs', params={'per_page': 1})
        if resp.status_code != 200:
            pytest.skip('Job listing endpoint not available')

        data = resp.json()
        # Handle both list and paginated-wrapper shapes
        jobs = data if isinstance(data, list) else data.get('items') or data.get('jobs') or []
        if not jobs:
            pytest.skip('No jobs available in the database for detail tests')
        return jobs[0].get('id') or jobs[0].get('job_id')

    def test_job_detail_returns_200(self, api_url, anon_session, first_job_id):
        resp = anon_session.get(f'{api_url}/jobs/{first_job_id}')
        assert resp.status_code == 200

    def test_job_detail_response_has_required_fields(self, api_url, anon_session, first_job_id):
        resp = anon_session.get(f'{api_url}/jobs/{first_job_id}')
        assert resp.status_code == 200
        data = resp.json()
        for field in ('id', 'title', 'organisation'):
            assert field in data, f'Missing field {field!r} in job detail response'

    def test_job_detail_nonexistent_returns_404(self, api_url, anon_session):
        fake_id = '00000000-0000-0000-0000-000000000000'
        resp = anon_session.get(f'{api_url}/jobs/{fake_id}')
        assert resp.status_code == 404


class TestFrontendJobPages:
    """Smoke-test the user-facing frontend job pages (HTML responses)."""

    def test_jobs_list_page_accessible(self, frontend_url, anon_session):
        resp = anon_session.get(f'{frontend_url}/jobs')
        # May redirect to login if authentication is required
        assert resp.status_code in (200, 302)

    def test_jobs_list_page_content_type(self, frontend_url, anon_session):
        resp = anon_session.get(f'{frontend_url}/jobs', allow_redirects=True)
        content_type = resp.headers.get('Content-Type', '')
        assert 'text/html' in content_type, (
            f'Expected HTML response, got Content-Type: {content_type!r}'
        )
