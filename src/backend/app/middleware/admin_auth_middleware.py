"""
Admin Auth Middleware — JWT helpers and authorization for admin users.

Usage:
    @bp.route('/admin-only')
    @jwt_required()
    @require_admin()
    def admin_view():
        ...

    @bp.route('/admin-create-user')
    @jwt_required()
    @require_admin_role('admin')
    def create_admin():
        ...

    @bp.route('/admin-edit')
    @jwt_required()
    @require_admin_permission('users', 'edit')
    def edit_user():
        admin = get_current_admin()
        ...

All admin decorators must be stacked beneath @jwt_required().
Admin JWTs are distinguished from regular user JWTs by having user_type='admin' in claims.
"""
from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity

from app.utils.constants import ErrorCode


# ---------------------------------------------------------------------------
# Admin authorization decorators
# ---------------------------------------------------------------------------

def require_admin():
    """
    Restrict a route to admin users only (not regular users).
    
    Checks that the JWT has user_type='admin' claim.
    Returns 403 FORBIDDEN if not an admin user.
    Must be stacked beneath @jwt_required().
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get('user_type') != 'admin':
                return _forbidden('Admin access required')
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_admin_role(*roles):
    """
    Restrict a route to admins with specific roles.
    
    Args:
        *roles: One or more role names ('admin', 'operator')
    
    Returns 403 FORBIDDEN if the admin's role is not in the allowed list.
    Must be stacked beneath @jwt_required() and after @require_admin().
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get('user_type') != 'admin':
                return _forbidden('Admin access required')
            
            admin_role = claims.get('role', '')
            if admin_role not in roles:
                return _forbidden(f'Requires one of these roles: {", ".join(roles)}')
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_admin_permission(resource, action):
    """
    Restrict a route to admins with specific permission.
    
    Args:
        resource: Resource name (e.g., 'jobs', 'users', 'content')
        action: Action name (e.g., 'create', 'edit', 'delete')
    
    Checks admin's permissions from JWT claims or database.
    Returns 403 FORBIDDEN if permission not granted.
    Must be stacked beneath @jwt_required() and after @require_admin().
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            admin = get_current_admin()
            if isinstance(admin, tuple):
                return admin  # propagate error response
            
            if not admin.has_permission(resource, action):
                return _forbidden(f'Missing permission: {resource}.{action}')
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Current admin helper
# ---------------------------------------------------------------------------

def get_current_admin():
    """
    Return the AdminUser ORM object for the authenticated admin request.
    
    Raises 401 (as a Flask response tuple) if:
    - Admin user is not found in the DB
    - Account is suspended, inactive, or locked
    - JWT is not for an admin user type
    
    Routes that call this should check the return type:
        admin_or_err = get_current_admin()
        if isinstance(admin_or_err, tuple):
            return admin_or_err   # propagate the error
    
    Requires an active app + request context with a verified JWT.
    """
    from app.extensions import db
    from app.models.admin import AdminUser

    claims = get_jwt()
    
    # Check if this is an admin JWT
    if claims.get('user_type') != 'admin':
        return _unauthorized('Invalid token type')
    
    admin_id = get_jwt_identity()
    if not admin_id:
        return _unauthorized('Invalid token')
    
    admin = db.session.get(AdminUser, admin_id)
    if not admin:
        return _unauthorized('Admin user not found')
    
    if admin.status != 'active':
        return _unauthorized(f'Admin account is {admin.status}')
    
    if admin.is_locked():
        return _unauthorized('Admin account is locked due to failed login attempts')
    
    return admin


# ---------------------------------------------------------------------------
# Error response helpers
# ---------------------------------------------------------------------------

def _unauthorized(message='Unauthorized'):
    """Return a 401 Unauthorized response."""
    return jsonify({
        'success': False,
        'error': {
            'code': ErrorCode.UNAUTHORIZED,
            'message': message,
        }
    }), 401


def _forbidden(message='Forbidden'):
    """Return a 403 Forbidden response."""
    return jsonify({
        'success': False,
        'error': {
            'code': ErrorCode.FORBIDDEN_PERMISSION_DENIED,
            'message': message,
        }
    }), 403
