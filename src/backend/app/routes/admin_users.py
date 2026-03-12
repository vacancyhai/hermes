"""
Admin User Management Routes

POST   /api/v1/admin/users                  — Create new admin user (admin role only)
GET    /api/v1/admin/users                  — List all admin users
GET    /api/v1/admin/users/<id>             — Get admin user details
PUT    /api/v1/admin/users/<id>             — Update admin user (admin role only)
DELETE /api/v1/admin/users/<id>             — Deactivate admin user (admin role only)
PUT    /api/v1/admin/users/<id>/permissions — Update permissions (admin role only)
PUT    /api/v1/admin/users/<id>/role        — Update role (admin role only)
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.middleware.admin_auth_middleware import (
    get_current_admin,
    require_admin,
    require_admin_role,
)
from app.middleware.rate_limiter import limiter
from app.routes._helpers import _d, _err, _flatten, _load_args, _load_json, _ok
from app.services.admin_service import (
    create_admin_user,
    delete_admin_user,
    get_admin_user,
    list_admin_users,
    log_admin_action,
    update_admin_permissions,
    update_admin_user,
)
from app.utils.constants import ErrorCode
from app.validators.admin_validator import (
    CreateAdminSchema,
    UpdateAdminPermissionsSchema,
    UpdateAdminRoleSchema,
    UpdateAdminSchema,
)
from marshmallow import Schema, fields, validate

bp = Blueprint('admin_users', __name__, url_prefix='/api/v1/admin/users')

# Schema instances
_create_schema = CreateAdminSchema()
_update_schema = UpdateAdminSchema()
_update_role_schema = UpdateAdminRoleSchema()
_update_permissions_schema = UpdateAdminPermissionsSchema()


class ListAdminUsersQuerySchema(Schema):
    role = fields.String(validate=validate.OneOf(['admin', 'operator']))
    status = fields.String(validate=validate.OneOf(['active', 'inactive', 'suspended']))
    page = fields.Integer(missing=1, validate=validate.Range(min=1))
    per_page = fields.Integer(missing=20, validate=validate.Range(min=1, max=100))


_list_query_schema = ListAdminUsersQuerySchema()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@bp.route('', methods=['POST'])
@jwt_required()
@require_admin_role('admin')
@limiter.limit('10 per hour')
def create_admin():
    """Create a new admin user. Only 'admin' role can create users."""
    data, err = _load_json(_create_schema)
    if err:
        return err

    current_admin = get_current_admin()
    if isinstance(current_admin, tuple):
        return current_admin

    try:
        admin = create_admin_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            full_name=data['full_name'],
            role=data['role'],
            permissions=data.get('permissions', {}),
            created_by_id=str(current_admin.id),
        )
    except ValueError as e:
        return _err(ErrorCode.VALIDATION_ERROR, str(e), 400)
    except Exception as e:
        return _err(ErrorCode.SERVER_ERROR, 'Failed to create admin user', 500)

    # Log action
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')
    log_admin_action(
        admin_id=str(current_admin.id),
        action='create_admin_user',
        resource_type='admin_user',
        resource_id=str(admin.id),
        details={'username': admin.username, 'role': admin.role},
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return _ok({'admin': _serialize_admin(admin)}, status=201)


@bp.route('', methods=['GET'])
@jwt_required()
@require_admin()
def list_admins():
    """List all admin users with optional filters."""
    query_params, err = _load_args(_list_query_schema)
    if err:
        return err

    try:
        result = list_admin_users(
            role=query_params.get('role'),
            status=query_params.get('status'),
            page=query_params['page'],
            per_page=query_params['per_page'],
        )
    except Exception as e:
        return _err(ErrorCode.SERVER_ERROR, 'Failed to list admin users', 500)

    return _ok(
        data={
            'admins': [_serialize_admin(a) for a in result['admins']],
        },
        meta={
            'pagination': {
                'page': result['page'],
                'per_page': result['per_page'],
                'total_pages': result['total_pages'],
                'total_items': result['total_items'],
            }
        }
    )


@bp.route('/<admin_id>', methods=['GET'])
@jwt_required()
@require_admin()
def get_admin(admin_id):
    """Get a specific admin user by ID."""
    try:
        admin = get_admin_user(admin_id)
    except ValueError as e:
        return _err(ErrorCode.NOT_FOUND, str(e), 404)
    except Exception as e:
        return _err(ErrorCode.SERVER_ERROR, 'Failed to get admin user', 500)

    return _ok({'admin': _serialize_admin(admin)})


@bp.route('/<admin_id>', methods=['PUT'])
@jwt_required()
@require_admin_role('admin')
def update_admin(admin_id):
    """Update an admin user. Only 'admin' role can update users."""
    data, err = _load_json(_update_schema)
    if err:
        return err

    current_admin = get_current_admin()
    if isinstance(current_admin, tuple):
        return current_admin

    try:
        admin = update_admin_user(
            admin_id=admin_id,
            email=data.get('email'),
            full_name=data.get('full_name'),
            status=data.get('status'),
            updated_by_id=str(current_admin.id),
        )
    except ValueError as e:
        return _err(ErrorCode.VALIDATION_ERROR, str(e), 400)
    except Exception as e:
        return _err(ErrorCode.SERVER_ERROR, 'Failed to update admin user', 500)

    # Log action
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')
    log_admin_action(
        admin_id=str(current_admin.id),
        action='update_admin_user',
        resource_type='admin_user',
        resource_id=admin_id,
        details={'updated_fields': list(data.keys())},
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return _ok({'admin': _serialize_admin(admin)})


@bp.route('/<admin_id>', methods=['DELETE'])
@jwt_required()
@require_admin_role('admin')
def delete_admin(admin_id):
    """Deactivate an admin user (soft delete). Only 'admin' role can delete."""
    current_admin = get_current_admin()
    if isinstance(current_admin, tuple):
        return current_admin

    # Prevent self-deletion
    if str(current_admin.id) == admin_id:
        return _err(ErrorCode.VALIDATION_ERROR, 'Cannot delete your own account', 400)

    try:
        delete_admin_user(admin_id, str(current_admin.id))
    except ValueError as e:
        return _err(ErrorCode.NOT_FOUND, str(e), 404)
    except Exception as e:
        return _err(ErrorCode.SERVER_ERROR, 'Failed to delete admin user', 500)

    # Log action
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')
    log_admin_action(
        admin_id=str(current_admin.id),
        action='delete_admin_user',
        resource_type='admin_user',
        resource_id=admin_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return _ok({'message': 'Admin user deactivated successfully'})


@bp.route('/<admin_id>/permissions', methods=['PUT'])
@jwt_required()
@require_admin_role('admin')
def update_permissions(admin_id):
    """Update admin user permissions. Only 'admin' role can update permissions."""
    data, err = _load_json(_update_permissions_schema)
    if err:
        return err

    current_admin = get_current_admin()
    if isinstance(current_admin, tuple):
        return current_admin

    try:
        admin = update_admin_permissions(
            admin_id=admin_id,
            permissions=data['permissions'],
            updated_by_id=str(current_admin.id),
        )
    except ValueError as e:
        return _err(ErrorCode.VALIDATION_ERROR, str(e), 400)
    except Exception as e:
        return _err(ErrorCode.SERVER_ERROR, 'Failed to update permissions', 500)

    # Log action
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')
    log_admin_action(
        admin_id=str(current_admin.id),
        action='update_admin_permissions',
        resource_type='admin_user',
        resource_id=admin_id,
        details={'new_permissions': data['permissions']},
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return _ok({'admin': _serialize_admin(admin)})


@bp.route('/<admin_id>/role', methods=['PUT'])
@jwt_required()
@require_admin_role('admin')
def update_role(admin_id):
    """Update admin user role. Only 'admin' role can update roles."""
    data, err = _load_json(_update_role_schema)
    if err:
        return err

    current_admin = get_current_admin()
    if isinstance(current_admin, tuple):
        return current_admin

    # Prevent changing own role
    if str(current_admin.id) == admin_id:
        return _err(ErrorCode.VALIDATION_ERROR, 'Cannot change your own role', 400)

    try:
        admin = update_admin_user(
            admin_id=admin_id,
            role=data['role'],
            updated_by_id=str(current_admin.id),
        )
    except ValueError as e:
        return _err(ErrorCode.VALIDATION_ERROR, str(e), 400)
    except Exception as e:
        return _err(ErrorCode.SERVER_ERROR, 'Failed to update role', 500)

    # Log action
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')
    log_admin_action(
        admin_id=str(current_admin.id),
        action='update_admin_role',
        resource_type='admin_user',
        resource_id=admin_id,
        details={'new_role': data['role']},
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return _ok({'admin': _serialize_admin(admin)})


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

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
        'failed_login_attempts': admin.failed_login_attempts,
        'last_login': _d(admin.last_login),
        'last_login_ip': str(admin.last_login_ip) if admin.last_login_ip else None,
        'created_at': _d(admin.created_at),
        'updated_at': _d(admin.updated_at),
    }
