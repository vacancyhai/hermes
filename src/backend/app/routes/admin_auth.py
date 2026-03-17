"""
Admin Authentication Routes

POST   /api/v1/admin/auth/login           — admin login, returns admin + token pair
POST   /api/v1/admin/auth/logout          — blocklist access token (JWT required)
POST   /api/v1/admin/auth/refresh         — rotate token pair (refresh JWT required)
POST   /api/v1/admin/auth/change-password — change password (JWT required)
GET    /api/v1/admin/auth/me              — get current admin info (JWT required)
"""
from flask import Blueprint, current_app, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

from app.extensions import db
from app.middleware.admin_auth_middleware import get_current_admin, require_admin
from app.middleware.rate_limiter import limiter
from app.routes._helpers import _d, _err, _flatten, _load_json, _ok
from app.services.admin_service import (
    authenticate_admin,
    log_admin_action,
    reset_failed_login_attempts,
    update_admin_password,
)
from app.utils.constants import ErrorCode
from app.validators.admin_validator import AdminChangePasswordSchema, AdminLoginSchema

bp = Blueprint('admin_auth', __name__, url_prefix='/api/v1/admin/auth')

# Schema instances
_login_schema = AdminLoginSchema()
_change_password_schema = AdminChangePasswordSchema()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@bp.route('/login', methods=['POST'])
@limiter.limit('5 per minute')
def login():
    """Admin login endpoint — authenticate and return tokens."""
    data, err = _load_json(_login_schema)
    if err:
        return err

    # Get IP and user agent for audit logging
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')

    try:
        admin = authenticate_admin(
            username=data['username'],
            password=data['password'],
            ip_address=ip_address,
            user_agent=user_agent,
        )
    except ValueError as e:
        return _err(ErrorCode.UNAUTHORIZED, str(e), 401)
    except Exception as e:
        return _err(ErrorCode.SERVER_ERROR, 'Login failed', 500)

    # Reset failed login attempts on successful login
    reset_failed_login_attempts(admin.id)

    # Issue tokens with admin-specific claims
    access_token, refresh_token = _issue_admin_tokens(admin)

    # Log successful login
    log_admin_action(
        admin_id=str(admin.id),
        action='login',
        resource_type='auth',
        details={'ip_address': ip_address},
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return _ok({
        'admin': _serialize_admin(admin),
        'access_token': access_token,
        'refresh_token': refresh_token,
    })


@bp.route('/logout', methods=['POST'])
@jwt_required()
@require_admin()
def logout():
    """Blocklist the current access token to log out."""
    jti = get_jwt()['jti']
    exp = get_jwt()['exp']
    
    # Calculate TTL for Redis (time until token expires)
    from datetime import datetime, timezone
    ttl = exp - int(datetime.now(timezone.utc).timestamp())
    
    if ttl > 0:
        current_app.redis.setex(f'token_blocklist:{jti}', ttl, '1')

    # Log logout action
    admin = get_current_admin()
    if not isinstance(admin, tuple):
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        log_admin_action(
            admin_id=str(admin.id),
            action='logout',
            resource_type='auth',
            ip_address=ip_address,
            user_agent=user_agent,
        )

    return _ok({'message': 'Logged out successfully'})


@bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
@require_admin()
def refresh():
    """Issue new access and refresh tokens."""
    identity = get_jwt_identity()
    
    # Verify this is an admin token
    from app.models.admin import AdminUser
    admin = db.session.get(AdminUser, identity)
    
    if not admin:
        return _err(ErrorCode.UNAUTHORIZED, 'Admin not found', 401)
    
    if admin.status != 'active':
        return _err(ErrorCode.UNAUTHORIZED, f'Admin account is {admin.status}', 401)
    
    if admin.is_locked():
        return _err(ErrorCode.UNAUTHORIZED, 'Account is locked', 401)

    # Issue fresh tokens
    access_token, refresh_token = _issue_admin_tokens(admin)

    return _ok({
        'access_token': access_token,
        'refresh_token': refresh_token,
    })


@bp.route('/change-password', methods=['POST'])
@jwt_required()
@require_admin()
def change_password():
    """Change admin password."""
    data, err = _load_json(_change_password_schema)
    if err:
        return err

    admin = get_current_admin()
    if isinstance(admin, tuple):
        return admin

    try:
        update_admin_password(
            admin_id=admin.id,
            current_password=data['current_password'],
            new_password=data['new_password'],
        )
    except ValueError as e:
        return _err(ErrorCode.VALIDATION_ERROR, str(e), 400)
    except Exception as e:
        return _err(ErrorCode.SERVER_ERROR, 'Failed to change password', 500)

    # Log password change
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')
    log_admin_action(
        admin_id=str(admin.id),
        action='change_password',
        resource_type='auth',
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return _ok({'message': 'Password changed successfully'})


@bp.route('/me', methods=['GET'])
@jwt_required()
@require_admin()
def get_me():
    """Get current authenticated admin user info."""
    admin = get_current_admin()
    if isinstance(admin, tuple):
        return admin

    return _ok({'admin': _serialize_admin(admin)})


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _issue_admin_tokens(admin):
    """Create and return (access_token, refresh_token) pair for admin."""
    additional_claims = {
        'user_type': 'admin',  # Distinguish from regular user tokens
        'role': admin.role,
        'email': admin.email,
    }
    access_token = create_access_token(
        identity=str(admin.id),
        additional_claims=additional_claims,
    )
    refresh_token = create_refresh_token(
        identity=str(admin.id),
        additional_claims={'user_type': 'admin'}
    )
    return access_token, refresh_token


def _serialize_admin(admin):
    """Convert AdminUser model to dict for API response."""
    return {
        'id': str(admin.id),
        'username': admin.username,
        'email': admin.email,
        'full_name': admin.full_name,
        'role': admin.role,
        'permissions': admin.permissions,
        'status': admin.status,
        'is_verified': admin.is_verified,
        'is_2fa_enabled': admin.is_2fa_enabled,
        'last_login': _d(admin.last_login),
        'created_at': _d(admin.created_at),
        'updated_at': _d(admin.updated_at),
    }
