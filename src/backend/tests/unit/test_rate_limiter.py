"""
Unit / functional tests for app/middleware/rate_limiter.py

Tests:
  - _rate_limit_key() returns remote IP when no JWT is present.
  - _rate_limit_key() returns 'user:<id>' when a valid JWT is present.
  - _rate_limit_key() falls back to IP on invalid/malformed tokens.
  - init_limiter() forwards REDIS_URL to RATELIMIT_STORAGE_URI.
  - limiter is importable as the shared singleton.
"""
from datetime import timedelta
from unittest.mock import patch

import fakeredis
import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from flask_limiter import Limiter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_jwt_app(fake_redis=None):
    """Minimal Flask app with JWT configured — needed to create/decode tokens."""
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SECRET_KEY='test-secret',
        JWT_SECRET_KEY='test-jwt-secret-long-enough',
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=15),
        RATELIMIT_ENABLED=False,
    )
    JWTManager(app)
    if fake_redis is not None:
        app.redis = fake_redis

    from app.middleware.rate_limiter import init_limiter
    init_limiter(app)

    return app


# ---------------------------------------------------------------------------
# Test: singleton / importability
# ---------------------------------------------------------------------------

class TestRateLimiterSingleton:
    def test_limiter_is_a_limiter_instance(self):
        from app.middleware.rate_limiter import limiter
        assert isinstance(limiter, Limiter)

    def test_limiter_is_same_object_on_repeated_import(self):
        from app.middleware.rate_limiter import limiter as l1
        from app.middleware.rate_limiter import limiter as l2
        assert l1 is l2


# ---------------------------------------------------------------------------
# Test: _rate_limit_key key function
# ---------------------------------------------------------------------------

class TestRateLimitKey:
    def test_returns_ip_without_jwt(self):
        """No Authorization header → falls back to remote IP."""
        from app.middleware.rate_limiter import _rate_limit_key
        app = _make_jwt_app()
        with app.test_request_context('/', environ_base={'REMOTE_ADDR': '10.0.0.1'}):
            key = _rate_limit_key()
        assert key == '10.0.0.1'

    def test_returns_user_key_with_valid_jwt(self):
        """Valid Bearer token → returns 'user:<identity>'."""
        from app.middleware.rate_limiter import _rate_limit_key
        app = _make_jwt_app()
        with app.app_context():
            token = create_access_token(
                identity='user-uuid-abc',
                additional_claims={'role': 'user'},
            )
        with app.test_request_context(
            '/',
            headers={'Authorization': f'Bearer {token}'},
            environ_base={'REMOTE_ADDR': '10.0.0.1'},
        ):
            key = _rate_limit_key()
        assert key == 'user:user-uuid-abc'

    def test_falls_back_to_ip_with_malformed_token(self):
        """Malformed token → exception caught → IP returned."""
        from app.middleware.rate_limiter import _rate_limit_key
        app = _make_jwt_app()
        with app.test_request_context(
            '/',
            headers={'Authorization': 'Bearer not-a-real-token'},
            environ_base={'REMOTE_ADDR': '192.168.1.5'},
        ):
            key = _rate_limit_key()
        assert key == '192.168.1.5'

    def test_falls_back_to_ip_with_no_authorization_header(self):
        """Absent header → no JWT identity → IP returned."""
        from app.middleware.rate_limiter import _rate_limit_key
        app = _make_jwt_app()
        with app.test_request_context(
            '/',
            environ_base={'REMOTE_ADDR': '172.16.0.1'},
        ):
            key = _rate_limit_key()
        assert key == '172.16.0.1'


# ---------------------------------------------------------------------------
# Test: init_limiter forwards REDIS_URL
# ---------------------------------------------------------------------------

class TestInitLimiter:
    def test_redis_url_forwarded_to_ratelimit_storage(self):
        app = Flask(__name__)
        app.config.update(
            TESTING=True,
            SECRET_KEY='s',
            REDIS_URL='redis://localhost:6379/1',
            RATELIMIT_ENABLED=False,
        )
        from app.middleware.rate_limiter import init_limiter
        init_limiter(app)
        assert app.config.get('RATELIMIT_STORAGE_URI') == 'redis://localhost:6379/1'

    def test_explicit_ratelimit_storage_uri_not_overwritten(self):
        app = Flask(__name__)
        app.config.update(
            TESTING=True,
            SECRET_KEY='s',
            REDIS_URL='redis://localhost:6379/1',
            RATELIMIT_STORAGE_URI='redis://other-host:6379/2',
            RATELIMIT_ENABLED=False,
        )
        from app.middleware.rate_limiter import init_limiter
        init_limiter(app)
        # Explicit value must not be overwritten
        assert app.config.get('RATELIMIT_STORAGE_URI') == 'redis://other-host:6379/2'
