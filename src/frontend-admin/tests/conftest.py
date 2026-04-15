"""Shared fixtures for admin frontend tests."""

import pytest
from unittest.mock import MagicMock

from app import create_app


@pytest.fixture
def app():
    application = create_app()
    application.config["TESTING"] = True
    application.config["SECRET_KEY"] = "test-secret"  # pragma: allowlist secret
    return application


@pytest.fixture
def mock_api(app):
    """Replace app.api_client with a MagicMock for each test."""
    mock = MagicMock()
    app.api_client = mock
    return mock


@pytest.fixture
def client(app, mock_api):
    return app.test_client()


@pytest.fixture
def auth_client(app, mock_api):
    """Test client with admin token already in session."""
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess["token"] = "admin-token"
            sess["admin_name"] = "Admin User"
            sess["admin_role"] = "admin"
            sess["csrf_token"] = "test-csrf"
        yield c, mock_api
