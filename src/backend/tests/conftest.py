"""
Shared pytest fixtures for backend tests.

The test Flask app:
  - Uses fakeredis so no real Redis is needed.
  - Does NOT initialise SQLAlchemy — service-level unit tests mock db.session
    directly; route-level integration tests mock the service module.
  - JWT is fully configured so token encoding/decoding works in route tests.
  - Rate limiting is disabled (RATELIMIT_ENABLED=False) so tests aren't throttled.
"""
from datetime import timedelta

import fakeredis
import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.middleware.auth_middleware import register_jwt_error_handlers, register_token_rotation
from app.routes.auth import bp as auth_bp


@pytest.fixture
def fake_redis():
    """In-process fakeredis instance, reset between tests."""
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def app(fake_redis):
    """Minimal Flask app wired with JWT + fakeredis + auth blueprint."""
    flask_app = Flask(__name__)
    flask_app.config.update(
        TESTING=True,
        SECRET_KEY='test-secret-key-that-is-long-enough',
        JWT_SECRET_KEY='test-jwt-secret-key-that-is-long-enough',
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=15),
        JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=7),
        RATELIMIT_ENABLED=False,  # disable rate limiting in tests
    )

    jwt = JWTManager(flask_app)
    flask_app.redis = fake_redis

    @jwt.token_in_blocklist_loader
    def check_blocklist(jwt_header, jwt_payload):
        jti = jwt_payload.get('jti')
        return flask_app.redis.get(f'blocklist:{jti}') is not None

    register_jwt_error_handlers(jwt)
    register_token_rotation(flask_app)

    # Attach shared limiter (disabled via RATELIMIT_ENABLED=False above)
    from app.middleware.rate_limiter import limiter
    limiter.init_app(flask_app)

    # Request ID middleware
    from app.middleware.request_id import register_request_id
    register_request_id(flask_app)

    flask_app.register_blueprint(auth_bp)

    from app.routes.jobs import bp as jobs_bp
    from app.routes.users import bp as users_bp
    flask_app.register_blueprint(jobs_bp)
    flask_app.register_blueprint(users_bp)

    return flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def access_token_for(app):
    """Factory: returns a valid access token for a given user_id + role."""
    def _make(user_id='test-user-id', role='user'):
        with app.app_context():
            return create_access_token(
                identity=user_id,
                additional_claims={'role': role, 'email': 'test@example.com'},
            )
    return _make


@pytest.fixture
def refresh_token_for(app):
    """Factory: returns a valid refresh token for a given user_id."""
    def _make(user_id='test-user-id'):
        with app.app_context():
            return create_refresh_token(identity=user_id)
    return _make


@pytest.fixture
def auth_header(access_token_for):
    """Returns Authorization header dict for a regular user."""
    return {'Authorization': f'Bearer {access_token_for()}'}


@pytest.fixture
def db_session(app):
    """
    Yields a SQLAlchemy session scoped to a savepoint that is rolled back
    at the end of every test, leaving the DB unmodified.

    Requires a real PostgreSQL connection (DATABASE_URL must be set).
    Integration tests that only mock the service layer do not need this.
    Mark such tests with @pytest.mark.integration to keep them opt-in.

    Uses begin_nested() (SAVEPOINT) which is SQLAlchemy 2.x compatible.
    Any commit() calls inside the test only release the savepoint; the
    outer transaction is always rolled back when the fixture tears down.
    """
    with app.app_context():
        from app.extensions import db as _db
        _db.session.begin_nested()
        yield _db.session
        _db.session.rollback()
        _db.session.remove()
