"""
Authentication Routes

POST   /api/v1/auth/register          — create account, returns user + token pair
POST   /api/v1/auth/login             — verify credentials, returns token pair
POST   /api/v1/auth/logout            — blocklist access token JTI  (JWT required)
POST   /api/v1/auth/refresh           — rotate token pair           (refresh JWT required)
POST   /api/v1/auth/forgot-password   — request password-reset email
POST   /api/v1/auth/reset-password    — submit new password with reset token
GET    /api/v1/auth/verify-email/<t>  — verify email address
"""
from flask import Blueprint, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app.middleware.rate_limiter import limiter
from app.routes._helpers import _err, _flatten, _load_json, _ok
from app.services import auth_service
from app.tasks.notification_tasks import (
    send_password_reset_email_task,
    send_verification_email_task,
)
from app.validators.auth_validator import (
    LoginSchema,
    PasswordResetRequestSchema,
    PasswordResetSchema,
    RegisterSchema,
)

bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')

# Schema instances (marshmallow schemas are stateless — safe to reuse)
_register_schema = RegisterSchema()
_login_schema = LoginSchema()
_reset_req_schema = PasswordResetRequestSchema()
_reset_schema = PasswordResetSchema()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@bp.route('/register', methods=['POST'])
@limiter.limit('5 per minute')
def register():
    data, err = _load_json(_register_schema)
    if err:
        return err

    try:
        user, access_token, refresh_token, _verify_token = auth_service.register(data)
    except ValueError as e:
        if str(e) == 'EMAIL_TAKEN':
            return _err('VALIDATION_EMAIL_EXISTS', 'An account with this email already exists.', 400)
        return _err('SERVER_ERROR', 'Registration failed.', 500)

    send_verification_email_task.delay(str(user.id), _verify_token)
    return _ok({
        'user': _serialize_user(user),
        'access_token': access_token,
        'refresh_token': refresh_token,
    }, 201)


@bp.route('/login', methods=['POST'])
@limiter.limit('5 per minute')
def login():
    data, err = _load_json(_login_schema)
    if err:
        return err

    try:
        user, access_token, refresh_token = auth_service.login(data['email'], data['password'])
    except ValueError as e:
        code = str(e)
        if code == 'INVALID_CREDENTIALS':
            return _err('AUTH_INVALID_CREDENTIALS', 'Invalid email or password.', 401)
        if code == 'ACCOUNT_SUSPENDED':
            return _err('AUTH_ACCOUNT_SUSPENDED', 'Your account has been suspended.', 401)
        return _err('SERVER_ERROR', 'Login failed.', 500)

    return _ok({
        'user': _serialize_user(user),
        'access_token': access_token,
        'refresh_token': refresh_token,
    })


@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    auth_service.logout(get_jwt()['jti'])
    return _ok({'message': 'Successfully logged out.'})


@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    try:
        access_token, refresh_token = auth_service.refresh(
            user_id=get_jwt_identity(),
            old_jti=get_jwt()['jti'],
        )
    except ValueError:
        return _err('AUTH_UNAUTHORIZED', 'Token refresh failed.', 401)

    return _ok({'access_token': access_token, 'refresh_token': refresh_token})


@bp.route('/forgot-password', methods=['POST'])
@limiter.limit('3 per minute')
def forgot_password():
    data, err = _load_json(_reset_req_schema)
    if err:
        return err

    _user, _reset_token = auth_service.request_password_reset(data['email'])
    if _user and _reset_token:
        send_password_reset_email_task.delay(str(_user.id), _reset_token)

    # Always return the same response — do not reveal whether the email exists
    return _ok({'message': 'If an account exists for this email, a reset link has been sent.'})


@bp.route('/reset-password', methods=['POST'])
@limiter.limit('5 per minute')
def reset_password():
    data, err = _load_json(_reset_schema)
    if err:
        return err

    try:
        auth_service.reset_password(data['token'], data['new_password'])
    except ValueError:
        return _err('AUTH_INVALID_TOKEN', 'Reset token is invalid or has expired.', 400)

    return _ok({'message': 'Password has been reset successfully.'})


@bp.route('/verify-email/<token>', methods=['GET'])
def verify_email(token):
    try:
        auth_service.verify_email(token)
    except ValueError:
        return _err('AUTH_INVALID_TOKEN', 'Verification token is invalid or has expired.', 400)

    return _ok({'message': 'Email verified successfully.'})


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _serialize_user(user):
    """Return safe user dict — never includes password_hash."""
    return {
        'id': str(user.id),
        'email': user.email,
        'full_name': user.full_name,
        'role': user.role,
        'is_email_verified': user.is_email_verified,
        'created_at': user.created_at.isoformat() if user.created_at else None,
    }
