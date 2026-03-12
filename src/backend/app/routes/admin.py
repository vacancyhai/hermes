"""
Admin Dashboard Routes

GET    /api/v1/admin/stats      — Get admin dashboard statistics
GET    /api/v1/admin/analytics  — Get admin analytics (to implement)
"""
from flask import Blueprint
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.middleware.admin_auth_middleware import require_admin
from app.models.admin import AdminLog, AdminUser
from app.models.job import JobVacancy
from app.models.user import User
from app.routes._helpers import _err, _ok
from app.utils.constants import ErrorCode

bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin')


@bp.route('/stats', methods=['GET'])
@jwt_required()
@require_admin()
def get_stats():
    """Get dashboard statistics for admin panel."""
    try:
        # Count users
        total_users = db.session.query(db.func.count(User.id)).scalar()
        active_users = db.session.query(db.func.count(User.id)).filter_by(status='active').scalar()
        
        # Count jobs
        total_jobs = db.session.query(db.func.count(JobVacancy.id)).scalar()
        active_jobs = db.session.query(db.func.count(JobVacancy.id)).filter_by(status='active').scalar()
        
        # Count admins
        total_admins = db.session.query(db.func.count(AdminUser.id)).scalar()
        active_admins = db.session.query(db.func.count(AdminUser.id)).filter_by(status='active').scalar()
        
        # Recent admin actions (last 24 hours)
        from datetime import datetime, timedelta, timezone
        yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_actions = db.session.query(db.func.count(AdminLog.id)).filter(
            AdminLog.timestamp >= yesterday
        ).scalar()
        
        stats = {
            'users': {
                'total': total_users,
                'active': active_users,
            },
            'jobs': {
                'total': total_jobs,
                'active': active_jobs,
            },
            'admins': {
                'total': total_admins,
                'active': active_admins,
            },
            'activity': {
                'recent_actions_24h': recent_actions,
            }
        }
        
        return _ok({'stats': stats})
        
    except Exception as e:
        return _err(ErrorCode.SERVER_ERROR, 'Failed to retrieve statistics', 500)


@bp.route('/analytics', methods=['GET'])
@jwt_required()
@require_admin()
def get_analytics():
    """Get detailed analytics — to be implemented."""
    return _err(ErrorCode.NOT_IMPLEMENTED, 'Analytics not yet implemented', 501)

