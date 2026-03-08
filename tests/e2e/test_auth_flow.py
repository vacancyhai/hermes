"""
E2E tests: user registration, login, and logout flows via the backend API.
"""
import pytest
import requests


class TestHealthCheck:
    """Sanity-check that all services are reachable before running auth tests."""

    def test_api_health(self, api_url, anon_session):
        resp = anon_session.get(f'{api_url}/health')
        assert resp.status_code == 200
        data = resp.json()
        assert data.get('status') == 'healthy'

    def test_frontend_health(self, frontend_url, anon_session):
        resp = anon_session.get(f'{frontend_url}/health')
        assert resp.status_code == 200

    def test_admin_health(self, admin_url, anon_session):
        resp = anon_session.get(f'{admin_url}/health')
        assert resp.status_code == 200


class TestRegistration:
    def test_register_new_user_succeeds(self, api_url, anon_session):
        import uuid
        email    = f'reg_{uuid.uuid4().hex[:8]}@test.invalid'
        password = 'StrongP@ss1!'
        resp = anon_session.post(f'{api_url}/auth/register', json={
            'full_name': 'Test Reg User',
            'email': email,
            'password': password,
        })
        assert resp.status_code == 201
        body = resp.json()
        assert 'access_token' in body
        assert 'refresh_token' in body

    def test_register_duplicate_email_fails(self, api_url, api_session):
        # api_session already registered its email; register again with same one
        email = None
        # Fetch profile to get the registered email
        profile_resp = api_session.get(f'{api_url}/profile')
        if profile_resp.status_code == 200:
            email = profile_resp.json().get('email')

        if email is None:
            pytest.skip('Could not retrieve registered user email from /profile')

        resp = api_session.post(f'{api_url}/auth/register', json={
            'full_name': 'Duplicate',
            'email': email,
            'password': 'AnotherP@ss1!',
        })
        # Expect 409 Conflict or 400 Bad Request
        assert resp.status_code in (400, 409)

    def test_register_invalid_email_fails(self, api_url, anon_session):
        resp = anon_session.post(f'{api_url}/auth/register', json={
            'full_name': 'Bad Email',
            'email': 'not-an-email',
            'password': 'StrongP@ss1!',
        })
        assert resp.status_code == 400

    def test_register_weak_password_fails(self, api_url, anon_session):
        import uuid
        resp = anon_session.post(f'{api_url}/auth/register', json={
            'full_name': 'Weak Pass',
            'email': f'weak_{uuid.uuid4().hex[:6]}@test.invalid',
            'password': '123',
        })
        assert resp.status_code == 400


class TestLogin:
    def test_login_with_valid_credentials(self, api_url, anon_session):
        import uuid
        email    = f'login_{uuid.uuid4().hex[:8]}@test.invalid'
        password = 'LoginP@ss1!'
        # Register first
        anon_session.post(f'{api_url}/auth/register', json={
            'full_name': 'Login Test',
            'email': email,
            'password': password,
        })
        # Login
        resp = anon_session.post(f'{api_url}/auth/login', json={
            'email': email,
            'password': password,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert 'access_token' in data
        assert 'refresh_token' in data

    def test_login_with_wrong_password_fails(self, api_url, anon_session, api_session):
        profile_resp = api_session.get(f'{api_url}/profile')
        if profile_resp.status_code != 200:
            pytest.skip('Could not retrieve registered user email')

        email = profile_resp.json().get('email')
        resp  = anon_session.post(f'{api_url}/auth/login', json={
            'email': email,
            'password': 'WrongP@ss999!',
        })
        assert resp.status_code in (400, 401)

    def test_login_with_nonexistent_email_fails(self, api_url, anon_session):
        resp = anon_session.post(f'{api_url}/auth/login', json={
            'email': 'nobody@test.invalid',
            'password': 'SomeP@ss1!',
        })
        assert resp.status_code in (400, 401, 404)


class TestProtectedEndpoints:
    def test_profile_accessible_when_authenticated(self, api_url, api_session):
        resp = api_session.get(f'{api_url}/profile')
        assert resp.status_code == 200

    def test_profile_requires_auth(self, api_url, anon_session):
        resp = anon_session.get(f'{api_url}/profile')
        assert resp.status_code == 401

    def test_logout_invalidates_token(self, api_url, anon_session):
        """Register + login + logout — subsequent request should be 401."""
        import uuid
        email    = f'lo_{uuid.uuid4().hex[:8]}@test.invalid'
        password = 'LogoutP@ss1!'
        anon_session.post(f'{api_url}/auth/register', json={
            'full_name': 'Logout Test',
            'email': email,
            'password': password,
        })
        login_resp = anon_session.post(f'{api_url}/auth/login', json={
            'email': email,
            'password': password,
        })
        assert login_resp.status_code == 200
        tokens = login_resp.json()
        access  = tokens['access_token']
        refresh = tokens.get('refresh_token', '')

        auth_header = {'Authorization': f'Bearer {access}'}

        # Logout
        logout_resp = anon_session.post(
            f'{api_url}/auth/logout',
            json={'refresh_token': refresh},
            headers=auth_header,
        )
        assert logout_resp.status_code in (200, 204)

        # Subsequent protected request should fail
        profile_resp = anon_session.get(
            f'{api_url}/profile',
            headers=auth_header,
        )
        assert profile_resp.status_code == 401
