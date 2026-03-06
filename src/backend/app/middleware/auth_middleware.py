"""
Auth middleware — JWT helpers, role enforcement, and token rotation.

Usage:
    @bp.route('/admin-only')
    @jwt_required()
    @require_role('admin')
    def admin_view():
        ...

    @bp.route('/me')
    @jwt_required()
    def me():
        user = get_current_user()   # fetches User from DB, raises 401 if suspended
        ...

Token rotation:
    register_token_rotation(app) must be called from create_app().
    If an access token has <= TOKEN_ROTATION_THRESHOLD_SECONDS remaining,
    a fresh access token is issued and returned in the X-New-Access-Token
    response header. The client should replace its stored token with this value.

@require_role must be applied *after* @jwt_required so that JWT claims are
already decoded and available via get_jwt().
"""
from datetime import datetime, timezone
from functools import wraps

from flask import current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    decode_token,
    get_jwt,
    get_jwt_identity,
)

TOKEN_ROTATION_THRESHOLD_SECONDS = 120  # issue new token if < 2 min left


# ---------------------------------------------------------------------------
# Role enforcement
# ---------------------------------------------------------------------------

def require_role(*roles):
    """
    Restrict a route to users whose JWT 'role' claim is in *roles*.

    Returns 403 FORBIDDEN_PERMISSION_DENIED if the role does not match.
    Must be stacked beneath @jwt_required().
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get('role', '') not in roles:
                return _forbidden()
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Current user helper
# ---------------------------------------------------------------------------

def get_current_user():
    """
    Return the User ORM object for the authenticated request.

    Raises 401 (as a Flask response tuple) if the user is not found in the DB
    or if their account is suspended/deleted.  Routes that call this should
    check the return type:

        user_or_err = get_current_user()
        if isinstance(user_or_err, tuple):
            return user_or_err   # propagate the 401

    Requires an active app + request context with a verified JWT.
    """
    from app.models.user import User

    user_id = get_jwt_identity()
    user = current_app.extensions['sqlalchemy'].session.get(User, user_id)

    if not user or user.status in ('suspended', 'deleted'):
        return _unauthorized('AUTH_UNAUTHORIZED', 'User account is inactive or does not exist.')

    return user


# ---------------------------------------------------------------------------
# Token rotation
# ---------------------------------------------------------------------------

def register_token_rotation(app):
    """
    Register an after_request hook that proactively rotates the access token
    when it is within TOKEN_ROTATION_THRESHOLD_SECONDS of expiry.

    Call once from create_app() after JWTManager is initialised.
    """
    @app.after_request
    def _rotate_if_near_expiry(response):
        # Only act on requests that carried a non-refresh access token
        try:
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return response

            raw_token = auth_header.split(' ', 1)[1]
            decoded = decode_token(raw_token)

            # Skip refresh tokens
            if decoded.get('type') == 'refresh':
                return response

            exp = decoded.get('exp')
            if exp is None:
                return response

            remaining = exp - datetime.now(timezone.utc).timestamp()
            if remaining <= TOKEN_ROTATION_THRESHOLD_SECONDS:
                claims = {k: v for k, v in decoded.items()
                          if k not in ('sub', 'iat', 'exp', 'nbf', 'jti', 'type', 'fresh')}
                new_token = create_access_token(
                    identity=decoded['sub'],
                    additional_claims=claims,
                )
                response.headers['X-New-Access-Token'] = new_token

        except Exception:
            # Never break a response due to rotation errors
            pass

        return response


# ---------------------------------------------------------------------------
# JWT error handlers (registered in create_app via register_jwt_error_handlers)
# ---------------------------------------------------------------------------

def register_jwt_error_handlers(jwt):
    """
    Override Flask-JWT-Extended's default error responses with our standard
    error envelope.  Call once from create_app() after JWTManager(app).
    """
    @jwt.expired_token_loader
    def expired_token(_header, _payload):
        return _unauthorized('AUTH_TOKEN_EXPIRED', 'Your session has expired. Please log in again.')

    @jwt.invalid_token_loader
    def invalid_token(_reason):
        return _unauthorized('AUTH_UNAUTHORIZED', 'Invalid authentication token.')

    @jwt.unauthorized_loader
    def missing_token(_reason):
        return _unauthorized('AUTH_UNAUTHORIZED', 'Authentication token is missing.')

    @jwt.revoked_token_loader
    def revoked_token(_header, _payload):
        return _unauthorized('AUTH_TOKEN_REVOKED', 'Token has been revoked. Please log in again.')

    @jwt.needs_fresh_token_loader
    def needs_fresh(_header, _payload):
        return _unauthorized('AUTH_UNAUTHORIZED', 'A fresh token is required.')


# ---------------------------------------------------------------------------
# Convenience accessors
# ---------------------------------------------------------------------------

def get_current_user_id():
    """Return the user ID string from the current JWT identity."""
    return get_jwt_identity()


def get_current_role():
    """Return the role string from the current JWT claims."""
    return get_jwt().get('role', '')


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _unauthorized(code, message):
    return jsonify({
        'success': False,
        'error': {
            'code': code,
            'message': message,
            'details': [],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'request_id': request.headers.get('X-Request-ID', ''),
        }
    }), 401


def _forbidden():
    return jsonify({
        'success': False,
        'error': {
            'code': 'FORBIDDEN_PERMISSION_DENIED',
            'message': 'You do not have permission to access this resource.',
            'details': [],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'request_id': request.headers.get('X-Request-ID', ''),
        }
    }), 403
