"""
Notification Routes

GET    /api/v1/notifications              — list own notifications (paginated)
GET    /api/v1/notifications/count        — unread count
PUT    /api/v1/notifications/<id>/read    — mark single notification read
PUT    /api/v1/notifications/read-all     — mark all notifications read
DELETE /api/v1/notifications/<id>         — delete a notification
"""
import uuid

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.middleware.rate_limiter import limiter
from app.routes._helpers import _err, _ok
from app.services import notification_service
from app.utils.constants import ErrorCode

bp = Blueprint('notifications', __name__, url_prefix='/api/v1/notifications')


def _is_valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@bp.route('', methods=['GET'])
@jwt_required()
@limiter.limit('60 per minute')
def list_notifications():
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    result = notification_service.get_notifications(user_id, page=page, per_page=per_page)
    return _ok(
        [_serialize(n) for n in result['items']],
        meta={
            'total': result['total'],
            'page': result['page'],
            'per_page': result['per_page'],
            'pages': result['pages'],
        },
    )


@bp.route('/count', methods=['GET'])
@jwt_required()
@limiter.limit('120 per minute')
def unread_count():
    user_id = get_jwt_identity()
    count = notification_service.get_unread_count(user_id)
    return _ok({'unread_count': count})


@bp.route('/<notification_id>/read', methods=['PUT'])
@jwt_required()
@limiter.limit('60 per minute')
def mark_read(notification_id):
    if not _is_valid_uuid(notification_id):
        return _err(ErrorCode.NOT_FOUND_NOTIFICATION, 'Notification not found.', 404)
    user_id = get_jwt_identity()
    try:
        notif = notification_service.mark_read(notification_id, user_id)
    except ValueError:
        return _err(ErrorCode.NOT_FOUND_NOTIFICATION, 'Notification not found.', 404)
    return _ok(_serialize(notif))


@bp.route('/read-all', methods=['PUT'])
@jwt_required()
@limiter.limit('30 per minute')
def mark_all_read():
    user_id = get_jwt_identity()
    updated = notification_service.mark_all_read(user_id)
    return _ok({'updated': updated})


@bp.route('/<notification_id>', methods=['DELETE'])
@jwt_required()
@limiter.limit('60 per minute')
def delete_notification(notification_id):
    if not _is_valid_uuid(notification_id):
        return _err(ErrorCode.NOT_FOUND_NOTIFICATION, 'Notification not found.', 404)
    user_id = get_jwt_identity()
    try:
        notification_service.delete_notification(notification_id, user_id)
    except ValueError:
        return _err(ErrorCode.NOT_FOUND_NOTIFICATION, 'Notification not found.', 404)
    return _ok({'message': 'Notification deleted.'})


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _serialize(notif) -> dict:
    return {
        'id': str(notif.id),
        'type': notif.type,
        'title': notif.title,
        'message': notif.message,
        'action_url': notif.action_url,
        'entity_type': notif.entity_type,
        'entity_id': str(notif.entity_id) if notif.entity_id else None,
        'is_read': notif.is_read,
        'priority': notif.priority,
        'created_at': notif.created_at.isoformat() if notif.created_at else None,
        'read_at': notif.read_at.isoformat() if notif.read_at else None,
    }


