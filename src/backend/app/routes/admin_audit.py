"""
Admin Audit Routes

GET    /api/v1/admin/audit/logs    — Get admin action logs
GET    /api/v1/admin/audit/access  — Get access audit logs
"""
from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.middleware.admin_auth_middleware import require_admin
from app.routes._helpers import _d, _err, _load_args, _ok
from app.services.admin_service import get_access_audit_logs, get_admin_logs
from app.utils.constants import ErrorCode
from app.validators.admin_validator import AccessAuditQuerySchema, AuditLogQuerySchema

bp = Blueprint('admin_audit', __name__, url_prefix='/api/v1/admin/audit')

# Schema instances
_audit_log_query_schema = AuditLogQuerySchema()
_access_audit_query_schema = AccessAuditQuerySchema()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@bp.route('/logs', methods=['GET'])
@jwt_required()
@require_admin()
def get_logs():
    """Get admin action logs with optional filters."""
    query_params, err = _load_args(_audit_log_query_schema)
    if err:
        return err

    try:
        result = get_admin_logs(
            admin_id=str(query_params['admin_id']) if query_params.get('admin_id') else None,
            action=query_params.get('action'),
            resource_type=query_params.get('resource_type'),
            start_date=query_params.get('start_date'),
            end_date=query_params.get('end_date'),
            page=query_params['page'],
            per_page=query_params['per_page'],
        )
    except Exception as e:
        return _err(ErrorCode.SERVER_ERROR, 'Failed to retrieve audit logs', 500)

    return _ok(
        data={
            'logs': [_serialize_admin_log(log) for log in result['admins']],
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


@bp.route('/access', methods=['GET'])
@jwt_required()
@require_admin()
def get_access_logs():
    """Get access audit logs with optional filters."""
    query_params, err = _load_args(_access_audit_query_schema)
    if err:
        return err

    try:
        result = get_access_audit_logs(
            admin_id=str(query_params['admin_id']) if query_params.get('admin_id') else None,
            ip_address=query_params.get('ip_address'),
            start_date=query_params.get('start_date'),
            end_date=query_params.get('end_date'),
            page=query_params['page'],
            per_page=query_params['per_page'],
        )
    except Exception as e:
        return _err(ErrorCode.SERVER_ERROR, 'Failed to retrieve access logs', 500)

    return _ok(
        data={
            'logs': [_serialize_access_log(log) for log in result['admins']],
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


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _serialize_admin_log(log):
    """Convert AdminLog model to dict for API response."""
    return {
        'id': str(log.id),
        'admin_id': str(log.admin_id),
        'action': log.action,
        'resource_type': log.resource_type,
        'resource_id': str(log.resource_id) if log.resource_id else None,
        'details': log.details,
        'changes': log.changes,
        'ip_address': str(log.ip_address) if log.ip_address else None,
        'user_agent': log.user_agent,
        'timestamp': _d(log.timestamp),
    }


def _serialize_access_log(log):
    """Convert AccessAuditLog model to dict for API response."""
    return {
        'id': str(log.id),
        'admin_id': str(log.admin_id),
        'action': log.action,
        'role': log.role,
        'resource': log.resource,
        'changes': log.changes,
        'reason': log.reason,
        'ip_address': str(log.ip_address) if log.ip_address else None,
        'timestamp': _d(log.timestamp),
    }
