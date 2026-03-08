"""
Integration tests for app/routes/jobs.py

Service layer is fully mocked — no DB or Redis needed.
Uses the shared `client` fixture from conftest (fakeredis + JWT + jobs blueprint).
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_job(**kwargs):
    job = MagicMock()
    job.id = kwargs.get('id', uuid.uuid4())
    job.job_title = kwargs.get('job_title', 'SSC CGL 2024')
    job.slug = kwargs.get('slug', 'ssc-cgl-2024')
    job.organization = kwargs.get('organization', 'SSC')
    job.department = None
    job.post_code = None
    job.job_type = kwargs.get('job_type', 'latest_job')
    job.employment_type = 'permanent'
    job.qualification_level = kwargs.get('qualification_level', 'graduate')
    job.total_vacancies = 500
    job.vacancy_breakdown = {}
    job.description = None
    job.short_description = None
    job.eligibility = {'qualification': 'graduate'}
    job.application_details = {}
    job.notification_date = None
    job.application_start = None
    job.application_end = None
    job.last_date_fee = None
    job.admit_card_release = None
    job.exam_start = None
    job.exam_end = None
    job.result_date = None
    job.exam_details = {}
    job.salary_initial = None
    job.salary_max = None
    job.salary = {}
    job.selection_process = []
    job.documents_required = []
    job.status = kwargs.get('status', 'active')
    job.is_featured = False
    job.is_urgent = False
    job.is_trending = False
    job.priority = 0
    job.views = 10
    job.applications_count = 5
    job.created_by = None
    job.published_at = None
    job.created_at = None
    job.updated_at = None
    return job


def _paginated(items, total=None):
    return {
        'items': items,
        'total': total if total is not None else len(items),
        'page': 1,
        'per_page': 20,
        'pages': 1,
    }


# ---------------------------------------------------------------------------
# GET /api/v1/jobs
# ---------------------------------------------------------------------------

class TestListJobs:
    ENDPOINT = '/api/v1/jobs'

    def test_returns_200_with_jobs_list(self, client):
        jobs = [_mock_job(), _mock_job(slug='upsc-cse')]
        with patch('app.routes.jobs.job_service.get_jobs') as mock_get:
            mock_get.return_value = _paginated(jobs)
            resp = client.get(self.ENDPOINT)

        assert resp.status_code == 200
        body = resp.get_json()
        assert body['success'] is True
        assert len(body['data']) == 2
        assert body['total'] == 2

    def test_returns_job_fields_in_response(self, client):
        job = _mock_job(job_title='RRB NTPC', organization='RRB')
        with patch('app.routes.jobs.job_service.get_jobs') as mock_get:
            mock_get.return_value = _paginated([job])
            resp = client.get(self.ENDPOINT)

        item = resp.get_json()['data'][0]
        assert item['job_title'] == 'RRB NTPC'
        assert item['organization'] == 'RRB'
        assert 'id' in item
        assert 'slug' in item

    def test_invalid_query_param_returns_400(self, client):
        resp = client.get(f'{self.ENDPOINT}?status=bogus')
        assert resp.status_code == 400
        assert resp.get_json()['error']['code'] == 'VALIDATION_ERROR'

    def test_valid_filters_passed_to_service(self, client):
        with patch('app.routes.jobs.job_service.get_jobs') as mock_get:
            mock_get.return_value = _paginated([])
            client.get(f'{self.ENDPOINT}?job_type=result&page=2')

        call_args = mock_get.call_args[0][0]
        assert call_args['job_type'] == 'result'
        assert call_args['page'] == 2


# ---------------------------------------------------------------------------
# GET /api/v1/jobs/<slug>
# ---------------------------------------------------------------------------

class TestGetJob:
    def test_returns_200_with_job_detail(self, client):
        job = _mock_job(slug='ssc-cgl-2024')
        with patch('app.routes.jobs.job_service.get_job_by_slug') as mock_get:
            mock_get.return_value = job
            resp = client.get('/api/v1/jobs/ssc-cgl-2024')

        assert resp.status_code == 200
        data = resp.get_json()['data']
        assert data['slug'] == 'ssc-cgl-2024'

    def test_returns_404_for_missing_slug(self, client):
        from app.utils.constants import ErrorCode

        with patch('app.routes.jobs.job_service.get_job_by_slug',
                   side_effect=ValueError(ErrorCode.NOT_FOUND_JOB)):
            resp = client.get('/api/v1/jobs/no-such-slug')

        assert resp.status_code == 404
        assert resp.get_json()['error']['code'] == ErrorCode.NOT_FOUND_JOB


# ---------------------------------------------------------------------------
# POST /api/v1/jobs
# ---------------------------------------------------------------------------

class TestCreateJob:
    ENDPOINT = '/api/v1/jobs'
    VALID_PAYLOAD = {
        'job_title': 'UPSC CSE 2024',
        'organization': 'UPSC',
        'job_type': 'latest_job',
        'eligibility': {'qualification': 'graduate'},
    }

    def _admin_headers(self, access_token_for):
        return {'Authorization': f'Bearer {access_token_for(role="admin")}'}

    def _user_headers(self, access_token_for):
        return {'Authorization': f'Bearer {access_token_for(role="user")}'}

    def test_operator_can_create_job(self, client, access_token_for):
        job = _mock_job(job_title='UPSC CSE 2024')
        headers = {'Authorization': f'Bearer {access_token_for(role="operator")}'}

        with patch('app.routes.jobs.job_service.create_job') as mock_create, \
             patch('app.tasks.notification_tasks.send_new_job_notifications') as mock_task:
            mock_create.return_value = job
            mock_task.delay = MagicMock()
            resp = client.post(self.ENDPOINT, json=self.VALID_PAYLOAD, headers=headers)

        assert resp.status_code == 201
        assert resp.get_json()['success'] is True

    def test_admin_can_create_job(self, client, access_token_for):
        job = _mock_job()
        headers = self._admin_headers(access_token_for)

        with patch('app.routes.jobs.job_service.create_job') as mock_create, \
             patch('app.tasks.notification_tasks.send_new_job_notifications') as mock_task:
            mock_create.return_value = job
            mock_task.delay = MagicMock()
            resp = client.post(self.ENDPOINT, json=self.VALID_PAYLOAD, headers=headers)

        assert resp.status_code == 201

    def test_regular_user_cannot_create_job(self, client, access_token_for):
        headers = self._user_headers(access_token_for)
        resp = client.post(self.ENDPOINT, json=self.VALID_PAYLOAD, headers=headers)
        assert resp.status_code == 403

    def test_unauthenticated_returns_401(self, client):
        resp = client.post(self.ENDPOINT, json=self.VALID_PAYLOAD)
        assert resp.status_code == 401

    def test_invalid_payload_returns_400(self, client, access_token_for):
        headers = self._admin_headers(access_token_for)
        resp = client.post(self.ENDPOINT, json={'job_title': 'Missing required fields'},
                           headers=headers)
        assert resp.status_code == 400
        assert resp.get_json()['error']['code'] == 'VALIDATION_ERROR'


# ---------------------------------------------------------------------------
# PUT /api/v1/jobs/<job_id>
# ---------------------------------------------------------------------------

class TestUpdateJob:
    def test_admin_can_update_job(self, client, access_token_for):
        job = _mock_job()
        job_id = str(job.id)
        headers = {'Authorization': f'Bearer {access_token_for(role="admin")}'}

        with patch('app.routes.jobs.job_service.update_job') as mock_upd:
            mock_upd.return_value = job
            resp = client.put(f'/api/v1/jobs/{job_id}',
                              json={'status': 'closed'}, headers=headers)

        assert resp.status_code == 200

    def test_not_found_returns_404(self, client, access_token_for):
        from app.utils.constants import ErrorCode
        headers = {'Authorization': f'Bearer {access_token_for(role="admin")}'}

        with patch('app.routes.jobs.job_service.update_job',
                   side_effect=ValueError(ErrorCode.NOT_FOUND_JOB)):
            resp = client.put(f'/api/v1/jobs/{uuid.uuid4()}',
                              json={'status': 'closed'}, headers=headers)

        assert resp.status_code == 404

    def test_regular_user_cannot_update(self, client, access_token_for):
        headers = {'Authorization': f'Bearer {access_token_for(role="user")}'}
        resp = client.put(f'/api/v1/jobs/{uuid.uuid4()}',
                          json={'status': 'closed'}, headers=headers)
        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# DELETE /api/v1/jobs/<job_id>
# ---------------------------------------------------------------------------

class TestDeleteJob:
    def test_admin_can_delete_job(self, client, access_token_for):
        headers = {'Authorization': f'Bearer {access_token_for(role="admin")}'}

        with patch('app.routes.jobs.job_service.delete_job'):
            resp = client.delete(f'/api/v1/jobs/{uuid.uuid4()}', headers=headers)

        assert resp.status_code == 200
        assert resp.get_json()['data']['message'] == 'Job archived successfully.'

    def test_operator_cannot_delete_job(self, client, access_token_for):
        headers = {'Authorization': f'Bearer {access_token_for(role="operator")}'}
        resp = client.delete(f'/api/v1/jobs/{uuid.uuid4()}', headers=headers)
        assert resp.status_code == 403

    def test_not_found_returns_404(self, client, access_token_for):
        from app.utils.constants import ErrorCode
        headers = {'Authorization': f'Bearer {access_token_for(role="admin")}'}

        with patch('app.routes.jobs.job_service.delete_job',
                   side_effect=ValueError(ErrorCode.NOT_FOUND_JOB)):
            resp = client.delete(f'/api/v1/jobs/{uuid.uuid4()}', headers=headers)

        assert resp.status_code == 404
