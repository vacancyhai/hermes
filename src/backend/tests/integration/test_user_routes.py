"""
Integration tests for app/routes/users.py

Service layer is fully mocked — no DB or Redis needed.
Uses the shared `client` fixture from conftest.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_user(**kwargs):
    user = MagicMock()
    user.id = kwargs.get('id', uuid.uuid4())
    user.email = kwargs.get('email', 'user@example.com')
    user.full_name = kwargs.get('full_name', 'Test User')
    user.phone = None
    user.role = kwargs.get('role', 'user')
    user.status = kwargs.get('status', 'active')
    user.is_email_verified = True
    user.last_login = None
    user.created_at = None
    return user


def _mock_profile(**kwargs):
    profile = MagicMock()
    profile.date_of_birth = None
    profile.gender = kwargs.get('gender', None)
    profile.category = None
    profile.is_pwd = False
    profile.is_ex_serviceman = False
    profile.state = kwargs.get('state', None)
    profile.city = None
    profile.pincode = None
    profile.highest_qualification = None
    profile.education = {}
    profile.physical_details = {}
    profile.notification_preferences = {}
    profile.updated_at = None
    return profile


def _mock_application(**kwargs):
    app = MagicMock()
    app.id = kwargs.get('id', uuid.uuid4())
    app.user_id = kwargs.get('user_id', uuid.uuid4())
    app.job_id = kwargs.get('job_id', uuid.uuid4())
    app.status = kwargs.get('status', 'applied')
    app.is_priority = False
    app.application_number = None
    app.exam_center = None
    app.notes = None
    app.applied_on = None
    return app


def _paginated(items, total=None):
    return {
        'items': items,
        'total': total if total is not None else len(items),
        'page': 1,
        'per_page': 20,
        'pages': 1,
    }


def _auth(access_token_for, role='user'):
    return {'Authorization': f'Bearer {access_token_for(role=role)}'}


# ---------------------------------------------------------------------------
# GET /api/v1/users/profile
# ---------------------------------------------------------------------------

class TestGetProfile:
    ENDPOINT = '/api/v1/users/profile'

    def test_returns_200_with_profile(self, client, access_token_for):
        user = _mock_user()
        profile = _mock_profile(gender='male', state='Delhi')

        with patch('app.routes.users.user_service.get_profile',
                   return_value=(user, profile)):
            resp = client.get(self.ENDPOINT, headers=_auth(access_token_for))

        assert resp.status_code == 200
        body = resp.get_json()
        assert body['success'] is True
        assert 'user' in body['data']
        assert 'profile' in body['data']
        assert body['data']['profile']['gender'] == 'male'

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(self.ENDPOINT)
        assert resp.status_code == 401

    def test_password_hash_not_in_response(self, client, access_token_for):
        user = _mock_user()
        profile = _mock_profile()

        with patch('app.routes.users.user_service.get_profile',
                   return_value=(user, profile)):
            resp = client.get(self.ENDPOINT, headers=_auth(access_token_for))

        flat = str(resp.get_json())
        assert 'password_hash' not in flat


# ---------------------------------------------------------------------------
# PUT /api/v1/users/profile
# ---------------------------------------------------------------------------

class TestUpdateProfile:
    ENDPOINT = '/api/v1/users/profile'

    def test_returns_200_with_updated_profile(self, client, access_token_for):
        user = _mock_user()
        profile = _mock_profile(gender='female')

        with patch('app.routes.users.user_service.update_profile',
                   return_value=(user, profile)):
            resp = client.put(self.ENDPOINT,
                              json={'gender': 'female'},
                              headers=_auth(access_token_for))

        assert resp.status_code == 200
        assert resp.get_json()['data']['profile']['gender'] == 'female'

    def test_invalid_gender_returns_400(self, client, access_token_for):
        resp = client.put(self.ENDPOINT,
                          json={'gender': 'unknown'},
                          headers=_auth(access_token_for))
        assert resp.status_code == 400
        assert resp.get_json()['error']['code'] == 'VALIDATION_ERROR'

    def test_invalid_pincode_returns_400(self, client, access_token_for):
        resp = client.put(self.ENDPOINT,
                          json={'pincode': 'abc'},
                          headers=_auth(access_token_for))
        assert resp.status_code == 400

    def test_unknown_field_returns_400(self, client, access_token_for):
        resp = client.put(self.ENDPOINT,
                          json={'unknown_field': 'bad'},
                          headers=_auth(access_token_for))
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/v1/users/applications
# ---------------------------------------------------------------------------

class TestListApplications:
    ENDPOINT = '/api/v1/users/applications'

    def test_returns_200_with_applications(self, client, access_token_for):
        apps = [_mock_application(), _mock_application()]
        with patch('app.routes.users.user_service.get_applications',
                   return_value=_paginated(apps)):
            resp = client.get(self.ENDPOINT, headers=_auth(access_token_for))

        assert resp.status_code == 200
        body = resp.get_json()
        assert body['success'] is True
        assert len(body['data']) == 2
        assert body['total'] == 2

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(self.ENDPOINT)
        assert resp.status_code == 401

    def test_application_fields_present(self, client, access_token_for):
        app = _mock_application(status='applied')
        with patch('app.routes.users.user_service.get_applications',
                   return_value=_paginated([app])):
            resp = client.get(self.ENDPOINT, headers=_auth(access_token_for))

        item = resp.get_json()['data'][0]
        assert 'id' in item
        assert 'job_id' in item
        assert 'status' in item


# ---------------------------------------------------------------------------
# POST /api/v1/users/applications
# ---------------------------------------------------------------------------

class TestApplyToJob:
    ENDPOINT = '/api/v1/users/applications'

    def test_returns_201_on_success(self, client, access_token_for):
        application = _mock_application()
        with patch('app.routes.users.user_service.apply_to_job',
                   return_value=application):
            resp = client.post(self.ENDPOINT,
                               json={'job_id': str(uuid.uuid4())},
                               headers=_auth(access_token_for))

        assert resp.status_code == 201
        assert resp.get_json()['success'] is True

    def test_missing_job_id_returns_400(self, client, access_token_for):
        resp = client.post(self.ENDPOINT, json={},
                           headers=_auth(access_token_for))
        assert resp.status_code == 400

    def test_job_not_found_returns_404(self, client, access_token_for):
        from app.utils.constants import ErrorCode

        with patch('app.routes.users.user_service.apply_to_job',
                   side_effect=ValueError(ErrorCode.NOT_FOUND_JOB)):
            resp = client.post(self.ENDPOINT,
                               json={'job_id': str(uuid.uuid4())},
                               headers=_auth(access_token_for))

        assert resp.status_code == 404

    def test_already_applied_returns_409(self, client, access_token_for):
        with patch('app.routes.users.user_service.apply_to_job',
                   side_effect=ValueError('ALREADY_APPLIED')):
            resp = client.post(self.ENDPOINT,
                               json={'job_id': str(uuid.uuid4())},
                               headers=_auth(access_token_for))

        assert resp.status_code == 409

    def test_unauthenticated_returns_401(self, client):
        resp = client.post(self.ENDPOINT, json={'job_id': str(uuid.uuid4())})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# DELETE /api/v1/users/applications/<app_id>
# ---------------------------------------------------------------------------

class TestWithdrawApplication:
    def test_returns_200_with_withdrawn_application(self, client, access_token_for):
        application = _mock_application(status='withdrawn')
        app_id = str(application.id)

        with patch('app.routes.users.user_service.withdraw_application',
                   return_value=application):
            resp = client.delete(f'/api/v1/users/applications/{app_id}',
                                 headers=_auth(access_token_for))

        assert resp.status_code == 200
        assert resp.get_json()['data']['status'] == 'withdrawn'

    def test_not_found_returns_404(self, client, access_token_for):
        from app.utils.constants import ErrorCode

        with patch('app.routes.users.user_service.withdraw_application',
                   side_effect=ValueError(ErrorCode.NOT_FOUND_APPLICATION)):
            resp = client.delete(f'/api/v1/users/applications/{uuid.uuid4()}',
                                 headers=_auth(access_token_for))

        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/v1/users  (admin)
# ---------------------------------------------------------------------------

class TestListUsers:
    ENDPOINT = '/api/v1/users'

    def test_admin_can_list_users(self, client, access_token_for):
        users = [_mock_user(), _mock_user(email='b@example.com')]
        with patch('app.routes.users.user_service.get_all_users',
                   return_value=_paginated(users)):
            resp = client.get(self.ENDPOINT, headers=_auth(access_token_for, role='admin'))

        assert resp.status_code == 200
        assert len(resp.get_json()['data']) == 2

    def test_regular_user_cannot_list_users(self, client, access_token_for):
        resp = client.get(self.ENDPOINT, headers=_auth(access_token_for, role='user'))
        assert resp.status_code == 403

    def test_unauthenticated_returns_401(self, client):
        resp = client.get(self.ENDPOINT)
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PUT /api/v1/users/<id>/status  (admin)
# ---------------------------------------------------------------------------

class TestUpdateUserStatus:
    def test_admin_can_suspend_user(self, client, access_token_for):
        user = _mock_user(status='suspended')
        user_id = str(uuid.uuid4())

        with patch('app.routes.users.user_service.update_user_status',
                   return_value=user):
            resp = client.put(f'/api/v1/users/{user_id}/status',
                              json={'status': 'suspended'},
                              headers=_auth(access_token_for, role='admin'))

        assert resp.status_code == 200
        assert resp.get_json()['data']['status'] == 'suspended'

    def test_invalid_status_value_returns_400(self, client, access_token_for):
        resp = client.put(f'/api/v1/users/{uuid.uuid4()}/status',
                          json={'status': 'banned'},
                          headers=_auth(access_token_for, role='admin'))
        assert resp.status_code == 400

    def test_missing_status_returns_400(self, client, access_token_for):
        resp = client.put(f'/api/v1/users/{uuid.uuid4()}/status',
                          json={},
                          headers=_auth(access_token_for, role='admin'))
        assert resp.status_code == 400

    def test_regular_user_cannot_update_status(self, client, access_token_for):
        resp = client.put(f'/api/v1/users/{uuid.uuid4()}/status',
                          json={'status': 'suspended'},
                          headers=_auth(access_token_for, role='user'))
        assert resp.status_code == 403

    def test_not_found_user_returns_404(self, client, access_token_for):
        from app.utils.constants import ErrorCode

        with patch('app.routes.users.user_service.update_user_status',
                   side_effect=ValueError(ErrorCode.NOT_FOUND_USER)):
            resp = client.put(f'/api/v1/users/{uuid.uuid4()}/status',
                              json={'status': 'suspended'},
                              headers=_auth(access_token_for, role='admin'))

        assert resp.status_code == 404
