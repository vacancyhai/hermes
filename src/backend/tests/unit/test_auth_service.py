"""
Unit tests for app/services/auth_service.py

DB calls are mocked via unittest.mock so no PostgreSQL is needed.
Redis calls use fakeredis (injected via the app fixture from conftest).
"""
import uuid
from datetime import timedelta
from unittest.mock import MagicMock, patch

import bcrypt
import fakeredis
import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, decode_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_app(fake_redis):
    """Minimal app context needed to call service functions."""
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        JWT_SECRET_KEY='test-jwt-secret',
        JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=15),
        JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=7),
        BCRYPT_LOG_ROUNDS=4,
    )
    JWTManager(app)
    app.redis = fake_redis
    return app


def _hashed(plain):
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=4)).decode()


def _mock_user(role='user', status='active', email='test@example.com'):
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = email
    user.role = role
    user.status = status
    user.password_hash = _hashed('correct_password')
    return user


# ---------------------------------------------------------------------------
# register()
# ---------------------------------------------------------------------------

class TestRegister:
    def test_creates_user_and_returns_tokens(self):
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        app = _make_app(fake_redis)

        mock_user = _mock_user()

        with app.app_context():
            with patch('app.services.auth_service.User') as MockUser, \
                 patch('app.services.auth_service.UserProfile') as MockProfile, \
                 patch('app.services.auth_service.db') as mock_db:

                MockUser.query.filter_by.return_value.first.return_value = None
                MockUser.return_value = mock_user

                user, access_token, refresh_token, verify_token = \
                    __import__('app.services.auth_service', fromlist=['register']).register({
                        'email': 'new@example.com',
                        'password': 'securepass',
                        'full_name': 'New User',
                    })

                assert user is mock_user
                assert access_token
                assert refresh_token
                assert verify_token
                mock_db.session.add.assert_called()
                mock_db.session.commit.assert_called_once()

    def test_raises_if_email_taken(self):
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        app = _make_app(fake_redis)

        with app.app_context():
            with patch('app.services.auth_service.User') as MockUser:
                MockUser.query.filter_by.return_value.first.return_value = _mock_user()

                from app.services.auth_service import register
                with pytest.raises(ValueError, match='EMAIL_TAKEN'):
                    register({'email': 'taken@example.com', 'password': 'pass1234', 'full_name': 'X'})

    def test_verify_token_stored_in_redis(self):
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        app = _make_app(fake_redis)
        mock_user = _mock_user()

        with app.app_context():
            with patch('app.services.auth_service.User') as MockUser, \
                 patch('app.services.auth_service.UserProfile'), \
                 patch('app.services.auth_service.db'):

                MockUser.query.filter_by.return_value.first.return_value = None
                MockUser.return_value = mock_user

                from app.services.auth_service import register
                _, _at, _rt, verify_token = register({'email': 'a@b.com', 'password': 'pass1234', 'full_name': 'A'})

                stored = fake_redis.get(f'email_verify:{verify_token}')
                assert stored == str(mock_user.id)


# ---------------------------------------------------------------------------
# login()
# ---------------------------------------------------------------------------

class TestLogin:
    def test_returns_tokens_on_valid_credentials(self):
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        app = _make_app(fake_redis)
        mock_user = _mock_user()

        with app.app_context():
            with patch('app.services.auth_service.User') as MockUser, \
                 patch('app.services.auth_service.db'):
                MockUser.query.filter_by.return_value.first.return_value = mock_user

                from app.services.auth_service import login
                access_token, refresh_token = login('test@example.com', 'correct_password')

                assert access_token
                assert refresh_token

    def test_raises_on_wrong_password(self):
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        app = _make_app(fake_redis)
        mock_user = _mock_user()

        with app.app_context():
            with patch('app.services.auth_service.User') as MockUser:
                MockUser.query.filter_by.return_value.first.return_value = mock_user

                from app.services.auth_service import login
                with pytest.raises(ValueError, match='INVALID_CREDENTIALS'):
                    login('test@example.com', 'wrong_password')

    def test_raises_on_unknown_email(self):
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        app = _make_app(fake_redis)

        with app.app_context():
            with patch('app.services.auth_service.User') as MockUser:
                MockUser.query.filter_by.return_value.first.return_value = None

                from app.services.auth_service import login
                with pytest.raises(ValueError, match='INVALID_CREDENTIALS'):
                    login('nobody@example.com', 'anypass')

    def test_raises_on_suspended_account(self):
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        app = _make_app(fake_redis)
        mock_user = _mock_user(status='suspended')

        with app.app_context():
            with patch('app.services.auth_service.User') as MockUser:
                MockUser.query.filter_by.return_value.first.return_value = mock_user

                from app.services.auth_service import login
                with pytest.raises(ValueError, match='ACCOUNT_SUSPENDED'):
                    login('test@example.com', 'correct_password')

    def test_updates_last_login(self):
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        app = _make_app(fake_redis)
        mock_user = _mock_user()

        with app.app_context():
            with patch('app.services.auth_service.User') as MockUser, \
                 patch('app.services.auth_service.db') as mock_db:
                MockUser.query.filter_by.return_value.first.return_value = mock_user

                from app.services.auth_service import login
                login('test@example.com', 'correct_password')

                assert mock_user.last_login is not None
                mock_db.session.commit.assert_called_once()


# ---------------------------------------------------------------------------
# logout()
# ---------------------------------------------------------------------------

class TestLogout:
    def test_stores_jti_in_redis_blocklist(self):
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        app = _make_app(fake_redis)

        with app.app_context():
            from app.services.auth_service import logout
            logout('some-jti-value')

        assert fake_redis.get('blocklist:some-jti-value') == '1'

    def test_blocklist_key_has_ttl(self):
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        app = _make_app(fake_redis)

        with app.app_context():
            from app.services.auth_service import logout
            logout('jti-123')

        ttl = fake_redis.ttl('blocklist:jti-123')
        assert ttl > 0


# ---------------------------------------------------------------------------
# refresh()
# ---------------------------------------------------------------------------

class TestRefresh:
    def test_blocklists_old_jti_and_returns_new_tokens(self):
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        app = _make_app(fake_redis)
        mock_user = _mock_user()

        with app.app_context():
            with patch('app.services.auth_service.db') as mock_db:
                mock_db.session.get.return_value = mock_user

                from app.services.auth_service import refresh
                access_token, refresh_token = refresh(str(mock_user.id), 'old-jti')

                assert access_token
                assert refresh_token
                assert fake_redis.get('blocklist:old-jti') == '1'

    def test_raises_if_user_not_found(self):
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        app = _make_app(fake_redis)

        with app.app_context():
            with patch('app.services.auth_service.db') as mock_db:
                mock_db.session.get.return_value = None

                from app.services.auth_service import refresh
                with pytest.raises(ValueError, match='USER_NOT_FOUND'):
                    refresh('bad-id', 'old-jti')

    def test_raises_if_user_suspended(self):
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        app = _make_app(fake_redis)
        mock_user = _mock_user(status='suspended')

        with app.app_context():
            with patch('app.services.auth_service.db') as mock_db:
                mock_db.session.get.return_value = mock_user

                from app.services.auth_service import refresh
                with pytest.raises(ValueError, match='USER_NOT_FOUND'):
                    refresh(str(mock_user.id), 'old-jti')


# ---------------------------------------------------------------------------
# request_password_reset()
# ---------------------------------------------------------------------------

class TestRequestPasswordReset:
    def test_stores_token_for_known_email(self):
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        app = _make_app(fake_redis)
        mock_user = _mock_user()

        with app.app_context():
            with patch('app.services.auth_service.User') as MockUser:
                MockUser.query.filter_by.return_value.first.return_value = mock_user

                from app.services.auth_service import request_password_reset
                user, token = request_password_reset('test@example.com')

                assert user is mock_user
                assert token
                assert fake_redis.get(f'pwd_reset:{token}') == str(mock_user.id)

    def test_returns_none_for_unknown_email(self):
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        app = _make_app(fake_redis)

        with app.app_context():
            with patch('app.services.auth_service.User') as MockUser:
                MockUser.query.filter_by.return_value.first.return_value = None

                from app.services.auth_service import request_password_reset
                user, token = request_password_reset('nobody@example.com')

                assert user is None
                assert token is None


# ---------------------------------------------------------------------------
# reset_password()
# ---------------------------------------------------------------------------

class TestResetPassword:
    def test_updates_password_and_deletes_token(self):
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        app = _make_app(fake_redis)
        mock_user = _mock_user()
        token = 'valid-reset-token'
        fake_redis.setex(f'pwd_reset:{token}', 3600, str(mock_user.id))

        with app.app_context():
            with patch('app.services.auth_service.db') as mock_db:
                mock_db.session.get.return_value = mock_user

                from app.services.auth_service import reset_password
                reset_password(token, 'new_secure_pass')

                assert bcrypt.checkpw(b'new_secure_pass', mock_user.password_hash.encode())
                mock_db.session.commit.assert_called_once()
                assert fake_redis.get(f'pwd_reset:{token}') is None

    def test_raises_on_invalid_token(self):
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        app = _make_app(fake_redis)

        with app.app_context():
            from app.services.auth_service import reset_password
            with pytest.raises(ValueError, match='INVALID_OR_EXPIRED_TOKEN'):
                reset_password('bad-token', 'newpass123')


# ---------------------------------------------------------------------------
# verify_email()
# ---------------------------------------------------------------------------

class TestVerifyEmail:
    def test_sets_email_verified_and_deletes_token(self):
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        app = _make_app(fake_redis)
        mock_user = _mock_user()
        token = 'valid-verify-token'
        fake_redis.setex(f'email_verify:{token}', 86400, str(mock_user.id))

        with app.app_context():
            with patch('app.services.auth_service.db') as mock_db:
                mock_db.session.get.return_value = mock_user

                from app.services.auth_service import verify_email
                user = verify_email(token)

                assert user.is_email_verified is True
                mock_db.session.commit.assert_called_once()
                assert fake_redis.get(f'email_verify:{token}') is None

    def test_raises_on_expired_token(self):
        fake_redis = fakeredis.FakeRedis(decode_responses=True)
        app = _make_app(fake_redis)

        with app.app_context():
            from app.services.auth_service import verify_email
            with pytest.raises(ValueError, match='INVALID_OR_EXPIRED_TOKEN'):
                verify_email('expired-token')
