"""
Shared fixtures for Hermes end-to-end tests.

Services under test are expected to already be running.
Use environment variables to override default URLs:

  HERMES_API_URL       — Backend REST API base  (default: http://localhost:5000/api/v1)
  HERMES_FRONTEND_URL  — User frontend base      (default: http://localhost:8080)
  HERMES_ADMIN_URL     — Admin frontend base     (default: http://localhost:8081)
"""
import os
import uuid

import pytest
import requests

# ---------------------------------------------------------------------------
# URL fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope='session')
def api_url() -> str:
    return os.environ.get('HERMES_API_URL', 'http://localhost:5000/api/v1').rstrip('/')


@pytest.fixture(scope='session')
def frontend_url() -> str:
    return os.environ.get('HERMES_FRONTEND_URL', 'http://localhost:8080').rstrip('/')


@pytest.fixture(scope='session')
def admin_url() -> str:
    return os.environ.get('HERMES_ADMIN_URL', 'http://localhost:8081').rstrip('/')


# ---------------------------------------------------------------------------
# HTTP sessions
# ---------------------------------------------------------------------------

@pytest.fixture
def anon_session() -> requests.Session:
    """Unauthenticated requests session."""
    with requests.Session() as s:
        yield s


@pytest.fixture
def api_session(api_url) -> requests.Session:
    """
    Authenticated API session.  Registers a throw-away user, logs in, attaches
    the JWT Authorization header, and cleans up after the test.
    """
    unique_suffix = uuid.uuid4().hex[:8]
    email    = f'e2e_user_{unique_suffix}@test.invalid'
    password = 'E2eTestP@ss1!'
    name     = f'E2E User {unique_suffix}'

    with requests.Session() as s:
        # Register
        reg = s.post(f'{api_url}/auth/register', json={
            'full_name': name,
            'email': email,
            'password': password,
        })
        assert reg.status_code == 201, f'Registration failed: {reg.text}'

        # Login
        login = s.post(f'{api_url}/auth/login', json={
            'email': email,
            'password': password,
        })
        assert login.status_code == 200, f'Login failed: {login.text}'

        tokens = login.json()
        access_token = tokens['access_token']
        s.headers.update({'Authorization': f'Bearer {access_token}'})
        s._e2e_refresh_token = tokens.get('refresh_token', '')  # type: ignore[attr-defined]
        s._e2e_api_url = api_url  # type: ignore[attr-defined]

        yield s

        # Cleanup — log out so the token is blocklisted
        try:
            s.post(f'{api_url}/auth/logout', json={
                'refresh_token': s._e2e_refresh_token  # type: ignore[attr-defined]
            })
        except requests.RequestException:
            pass
