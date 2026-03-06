"""
Integration tests for app/routes/auth.py

The service layer is fully mocked so no DB or Redis is needed beyond what
the conftest app provides (fakeredis for JWT blocklist checks).
"""
from unittest.mock import MagicMock, patch
import uuid


def _mock_user(**kwargs):
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = kwargs.get('email', 'new@example.com')
    user.full_name = kwargs.get('full_name', 'New User')
    user.role = kwargs.get('role', 'user')
    user.is_email_verified = False
    user.created_at = None
    return user


# ---------------------------------------------------------------------------
# POST /api/v1/auth/register
# ---------------------------------------------------------------------------

class TestRegisterRoute:
    ENDPOINT = '/api/v1/auth/register'
    VALID_PAYLOAD = {
        'email': 'new@example.com',
        'password': 'securepass123',
        'full_name': 'New User',
    }

    def test_success_returns_201_with_user_and_tokens(self, client):
        user = _mock_user()
        with patch('app.routes.auth.auth_service.register') as mock_reg:
            mock_reg.return_value = (user, 'access-tok', 'refresh-tok', 'verify-tok')
            resp = client.post(self.ENDPOINT, json=self.VALID_PAYLOAD)

        assert resp.status_code == 201
        body = resp.get_json()
        assert body['success'] is True
        assert 'access_token' in body['data']
        assert 'refresh_token' in body['data']
        assert 'user' in body['data']
        # password_hash must NOT be in response
        assert 'password_hash' not in body['data']['user']

    def test_user_object_has_expected_fields(self, client):
        user = _mock_user(email='a@b.com', full_name='Alice')
        with patch('app.routes.auth.auth_service.register') as mock_reg:
            mock_reg.return_value = (user, 'a', 'r', 'v')
            resp = client.post(self.ENDPOINT, json=self.VALID_PAYLOAD)

        u = resp.get_json()['data']['user']
        assert u['email'] == str(user.email)
        assert u['full_name'] == user.full_name
        assert 'id' in u
        assert 'role' in u

    def test_duplicate_email_returns_400_validation_email_exists(self, client):
        with patch('app.routes.auth.auth_service.register') as mock_reg:
            mock_reg.side_effect = ValueError('EMAIL_TAKEN')
            resp = client.post(self.ENDPOINT, json=self.VALID_PAYLOAD)

        assert resp.status_code == 400
        assert resp.get_json()['error']['code'] == 'VALIDATION_EMAIL_EXISTS'

    def test_missing_email_returns_400(self, client):
        resp = client.post(self.ENDPOINT, json={'password': 'pass1234', 'full_name': 'Jane'})
        assert resp.status_code == 400
        assert resp.get_json()['error']['code'] == 'VALIDATION_ERROR'

    def test_short_password_returns_400(self, client):
        resp = client.post(self.ENDPOINT, json={
            'email': 'u@e.com', 'password': 'short', 'full_name': 'Jane',
        })
        assert resp.status_code == 400

    def test_unknown_field_returns_400(self, client):
        payload = {**self.VALID_PAYLOAD, 'role': 'admin'}
        resp = client.post(self.ENDPOINT, json=payload)
        assert resp.status_code == 400

    def test_empty_body_returns_400(self, client):
        resp = client.post(self.ENDPOINT, json={})
        assert resp.status_code == 400

    def test_error_envelope_has_required_keys(self, client):
        resp = client.post(self.ENDPOINT, json={})
        body = resp.get_json()
        assert body['success'] is False
        assert {'code', 'message', 'timestamp', 'details'}.issubset(body['error'])


# ---------------------------------------------------------------------------
# POST /api/v1/auth/login
# ---------------------------------------------------------------------------

class TestLoginRoute:
    ENDPOINT = '/api/v1/auth/login'
    VALID_PAYLOAD = {'email': 'user@example.com', 'password': 'correct_pass'}

    def test_success_returns_200_with_tokens(self, client):
        with patch('app.routes.auth.auth_service.login') as mock_login:
            mock_login.return_value = ('access-tok', 'refresh-tok')
            resp = client.post(self.ENDPOINT, json=self.VALID_PAYLOAD)

        assert resp.status_code == 200
        body = resp.get_json()
        assert body['success'] is True
        assert body['data']['access_token'] == 'access-tok'
        assert body['data']['refresh_token'] == 'refresh-tok'

    def test_wrong_password_returns_401_auth_invalid_credentials(self, client):
        with patch('app.routes.auth.auth_service.login') as mock_login:
            mock_login.side_effect = ValueError('INVALID_CREDENTIALS')
            resp = client.post(self.ENDPOINT, json=self.VALID_PAYLOAD)

        assert resp.status_code == 401
        assert resp.get_json()['error']['code'] == 'AUTH_INVALID_CREDENTIALS'

    def test_suspended_account_returns_401_auth_account_suspended(self, client):
        with patch('app.routes.auth.auth_service.login') as mock_login:
            mock_login.side_effect = ValueError('ACCOUNT_SUSPENDED')
            resp = client.post(self.ENDPOINT, json=self.VALID_PAYLOAD)

        assert resp.status_code == 401
        assert resp.get_json()['error']['code'] == 'AUTH_ACCOUNT_SUSPENDED'

    def test_missing_password_returns_400(self, client):
        resp = client.post(self.ENDPOINT, json={'email': 'u@e.com'})
        assert resp.status_code == 400

    def test_invalid_email_format_returns_400(self, client):
        resp = client.post(self.ENDPOINT, json={'email': 'bad', 'password': 'pass'})
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/v1/auth/logout
# ---------------------------------------------------------------------------

class TestLogoutRoute:
    ENDPOINT = '/api/v1/auth/logout'

    def test_success_returns_200(self, client, auth_header):
        with patch('app.routes.auth.auth_service.logout'):
            resp = client.post(self.ENDPOINT, headers=auth_header)

        assert resp.status_code == 200
        assert resp.get_json()['success'] is True

    def test_no_token_returns_401(self, client):
        resp = client.post(self.ENDPOINT)
        assert resp.status_code == 401
        assert resp.get_json()['error']['code'] == 'AUTH_UNAUTHORIZED'

    def test_blocklisted_token_returns_401(self, client, app, access_token_for):
        token = access_token_for()
        from flask_jwt_extended import decode_token
        with app.app_context():
            decoded = decode_token(token)
            app.redis.set(f"blocklist:{decoded['jti']}", '1')

        resp = client.post(self.ENDPOINT, headers={'Authorization': f'Bearer {token}'})
        assert resp.status_code == 401
        assert resp.get_json()['error']['code'] == 'AUTH_TOKEN_REVOKED'


# ---------------------------------------------------------------------------
# POST /api/v1/auth/refresh
# ---------------------------------------------------------------------------

class TestRefreshRoute:
    ENDPOINT = '/api/v1/auth/refresh'

    def test_success_returns_new_tokens(self, client, refresh_token_for):
        token = refresh_token_for()
        with patch('app.routes.auth.auth_service.refresh') as mock_refresh:
            mock_refresh.return_value = ('new-access', 'new-refresh')
            resp = client.post(
                self.ENDPOINT,
                headers={'Authorization': f'Bearer {token}'},
            )

        assert resp.status_code == 200
        body = resp.get_json()
        assert body['data']['access_token'] == 'new-access'
        assert body['data']['refresh_token'] == 'new-refresh'

    def test_access_token_rejected_as_refresh(self, client, auth_header):
        # Custom invalid_token_loader returns 401 (not the default 422)
        resp = client.post(self.ENDPOINT, headers=auth_header)
        assert resp.status_code == 401
        assert resp.get_json()['error']['code'] == 'AUTH_UNAUTHORIZED'

    def test_no_token_returns_401(self, client):
        resp = client.post(self.ENDPOINT)
        assert resp.status_code == 401

    def test_service_error_returns_401(self, client, refresh_token_for):
        token = refresh_token_for()
        with patch('app.routes.auth.auth_service.refresh') as mock_refresh:
            mock_refresh.side_effect = ValueError('USER_NOT_FOUND')
            resp = client.post(
                self.ENDPOINT,
                headers={'Authorization': f'Bearer {token}'},
            )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /api/v1/auth/forgot-password
# ---------------------------------------------------------------------------

class TestForgotPasswordRoute:
    ENDPOINT = '/api/v1/auth/forgot-password'

    def test_known_email_returns_200(self, client):
        with patch('app.routes.auth.auth_service.request_password_reset') as mock_req:
            mock_req.return_value = (object(), 'reset-token')
            resp = client.post(self.ENDPOINT, json={'email': 'user@example.com'})

        assert resp.status_code == 200
        assert 'reset link' in resp.get_json()['data']['message']

    def test_unknown_email_still_returns_200(self, client):
        with patch('app.routes.auth.auth_service.request_password_reset') as mock_req:
            mock_req.return_value = (None, None)
            resp = client.post(self.ENDPOINT, json={'email': 'nobody@example.com'})

        assert resp.status_code == 200

    def test_invalid_email_returns_400(self, client):
        resp = client.post(self.ENDPOINT, json={'email': 'not-an-email'})
        assert resp.status_code == 400

    def test_missing_email_returns_400(self, client):
        resp = client.post(self.ENDPOINT, json={})
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/v1/auth/reset-password
# ---------------------------------------------------------------------------

class TestResetPasswordRoute:
    ENDPOINT = '/api/v1/auth/reset-password'

    def test_success_returns_200(self, client):
        with patch('app.routes.auth.auth_service.reset_password') as mock_reset:
            resp = client.post(self.ENDPOINT, json={
                'token': 'valid-token',
                'new_password': 'newpassword123',
            })

        assert resp.status_code == 200
        mock_reset.assert_called_once_with('valid-token', 'newpassword123')

    def test_invalid_token_returns_400_auth_invalid_token(self, client):
        with patch('app.routes.auth.auth_service.reset_password') as mock_reset:
            mock_reset.side_effect = ValueError('INVALID_OR_EXPIRED_TOKEN')
            resp = client.post(self.ENDPOINT, json={
                'token': 'bad-token',
                'new_password': 'newpassword123',
            })

        assert resp.status_code == 400
        assert resp.get_json()['error']['code'] == 'AUTH_INVALID_TOKEN'

    def test_short_password_returns_400(self, client):
        resp = client.post(self.ENDPOINT, json={'token': 'tok', 'new_password': 'short'})
        assert resp.status_code == 400

    def test_missing_token_returns_400(self, client):
        resp = client.post(self.ENDPOINT, json={'new_password': 'newpassword123'})
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# GET /api/v1/auth/verify-email/<token>
# ---------------------------------------------------------------------------

class TestVerifyEmailRoute:
    def test_valid_token_returns_200(self, client):
        with patch('app.routes.auth.auth_service.verify_email'):
            resp = client.get('/api/v1/auth/verify-email/valid-token')

        assert resp.status_code == 200
        assert 'verified' in resp.get_json()['data']['message'].lower()

    def test_invalid_token_returns_400_auth_invalid_token(self, client):
        with patch('app.routes.auth.auth_service.verify_email') as mock_verify:
            mock_verify.side_effect = ValueError('INVALID_OR_EXPIRED_TOKEN')
            resp = client.get('/api/v1/auth/verify-email/bad-token')

        assert resp.status_code == 400
        assert resp.get_json()['error']['code'] == 'AUTH_INVALID_TOKEN'


# ---------------------------------------------------------------------------
# JWT error handler responses (registered in auth_middleware)
# ---------------------------------------------------------------------------

class TestJWTErrorHandlers:
    def test_missing_token_returns_401_auth_unauthorized(self, client):
        resp = client.post('/api/v1/auth/logout')
        assert resp.status_code == 401
        assert resp.get_json()['error']['code'] == 'AUTH_UNAUTHORIZED'

    def test_revoked_token_returns_401_auth_token_revoked(self, client, app, access_token_for):
        token = access_token_for()
        from flask_jwt_extended import decode_token
        with app.app_context():
            decoded = decode_token(token)
            app.redis.set(f"blocklist:{decoded['jti']}", '1')

        resp = client.post('/api/v1/auth/logout', headers={'Authorization': f'Bearer {token}'})
        assert resp.status_code == 401
        assert resp.get_json()['error']['code'] == 'AUTH_TOKEN_REVOKED'

    def test_require_role_wrong_role_returns_403(self, client, access_token_for):
        # /logout is not role-gated, so hit a hypothetical protected route
        # by checking the @require_role decorator directly via middleware test
        from app.middleware.auth_middleware import require_role
        from flask import Flask
        from flask_jwt_extended import JWTManager, jwt_required

        mini = Flask('mini')
        mini.config.update(
            TESTING=True,
            JWT_SECRET_KEY='test-jwt-secret-key-that-is-long-enough',
        )
        JWTManager(mini)

        @mini.route('/admin-only')
        @jwt_required()
        @require_role('admin')
        def admin_only():
            return 'ok', 200

        with mini.test_client() as c:
            token = access_token_for(role='user')  # user, not admin
            resp = c.get('/admin-only', headers={'Authorization': f'Bearer {token}'})
            assert resp.status_code == 403
            assert resp.get_json()['error']['code'] == 'FORBIDDEN_PERMISSION_DENIED'
