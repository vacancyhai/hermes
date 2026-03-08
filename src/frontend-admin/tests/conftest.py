"""
Shared pytest fixtures for admin frontend tests.

No real backend is needed — APIClient calls are mocked in each test.
"""
import pytest
from unittest.mock import patch


@pytest.fixture
def app():
    """Minimal Flask app using the real create_app factory."""
    from app import create_app
    flask_app = create_app()
    flask_app.config.update(
        TESTING=True,
        SECRET_KEY='test-secret-key-32-chars-minimum!!',
        WTF_CSRF_ENABLED=False,
        BACKEND_API_URL='http://test-backend/api/v1',
    )
    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def app_ctx(app):
    """Push an application context so url_for / current_app work in unit tests."""
    with app.app_context():
        yield app


@pytest.fixture
def fake_login_data():
    """Simulates api_data from a successful admin login (no user field)."""
    import base64, json
    payload = base64.urlsafe_b64encode(
        json.dumps({"sub": "uid-admin-1", "role": "admin", "email": "admin@example.com"}).encode()
    ).rstrip(b"=").decode()
    token = f"eyJhbGciOiJIUzI1NiJ9.{payload}.fakesig"
    return {
        "access_token": token,
        "refresh_token": "refresh.token.here",
    }


@pytest.fixture
def fake_operator_data():
    """Simulates api_data from a successful operator login."""
    import base64, json
    payload = base64.urlsafe_b64encode(
        json.dumps({"sub": "uid-op-1", "role": "operator", "email": "op@example.com"}).encode()
    ).rstrip(b"=").decode()
    token = f"eyJhbGciOiJIUzI1NiJ9.{payload}.fakesig"
    return {
        "access_token": token,
        "refresh_token": "refresh.token.here",
    }


@pytest.fixture
def fake_user_data():
    """Simulates api_data for a plain user — should be rejected by the admin frontend."""
    import base64, json
    payload = base64.urlsafe_b64encode(
        json.dumps({"sub": "uid-user-1", "role": "user", "email": "user@example.com"}).encode()
    ).rstrip(b"=").decode()
    token = f"eyJhbGciOiJIUzI1NiJ9.{payload}.fakesig"
    return {
        "access_token": token,
        "refresh_token": "refresh.token.here",
    }
