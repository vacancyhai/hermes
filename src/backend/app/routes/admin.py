"""
Admin Dashboard Routes

GET    /api/v1/admin/stats      — Get admin dashboard statistics
GET    /api/v1/admin/analytics  — Get detailed analytics (jobs, users, notifications, applications)
"""
from datetime import datetime, timedelta, timezone

from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func, text

from app.extensions import db
from app.middleware.admin_auth_middleware import require_admin
from app.models.admin import AdminLog, AdminUser
from app.models.job import JobVacancy, UserJobApplication
from app.models.notification import Notification
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
        total_users = db.session.query(func.count(User.id)).scalar()
        active_users = db.session.query(func.count(User.id)).filter_by(status='active').scalar()

        total_jobs = db.session.query(func.count(JobVacancy.id)).scalar()
        active_jobs = db.session.query(func.count(JobVacancy.id)).filter_by(status='active').scalar()

        total_admins = db.session.query(func.count(AdminUser.id)).scalar()
        active_admins = db.session.query(func.count(AdminUser.id)).filter_by(status='active').scalar()

        yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_actions = db.session.query(func.count(AdminLog.id)).filter(
            AdminLog.timestamp >= yesterday
        ).scalar()

        stats = {
            'users': {'total': total_users, 'active': active_users},
            'jobs': {'total': total_jobs, 'active': active_jobs},
            'admins': {'total': total_admins, 'active': active_admins},
            'activity': {'recent_actions_24h': recent_actions},
        }

        return _ok({'stats': stats})

    except Exception:
        return _err(ErrorCode.SERVER_ERROR, 'Failed to retrieve statistics', 500)


@bp.route('/analytics', methods=['GET'])
@jwt_required()
@require_admin()
def get_analytics():
    """
    Detailed analytics for the admin dashboard.

    Query params:
        days  — number of days for trend data (default 30, max 90)
    """
    try:
        days = min(int(request.args.get('days', 30)), 90)
        since = datetime.now(timezone.utc) - timedelta(days=days)

        # 1. Job counts by type
        job_by_type = db.session.query(
            JobVacancy.job_type,
            func.count(JobVacancy.id).label('count')
        ).group_by(JobVacancy.job_type).all()

        # 2. Active jobs by status
        job_by_status = db.session.query(
            JobVacancy.status,
            func.count(JobVacancy.id).label('count')
        ).group_by(JobVacancy.status).all()

        # 3. Jobs posted per day (last N days) — cast to date then group
        jobs_per_day = db.session.query(
            func.date_trunc('day', JobVacancy.created_at).label('day'),
            func.count(JobVacancy.id).label('count')
        ).filter(
            JobVacancy.created_at >= since
        ).group_by(
            func.date_trunc('day', JobVacancy.created_at)
        ).order_by(
            func.date_trunc('day', JobVacancy.created_at)
        ).all()

        # 4. User registrations per day (last N days)
        users_per_day = db.session.query(
            func.date_trunc('day', User.created_at).label('day'),
            func.count(User.id).label('count')
        ).filter(
            User.created_at >= since
        ).group_by(
            func.date_trunc('day', User.created_at)
        ).order_by(
            func.date_trunc('day', User.created_at)
        ).all()

        # 5. Top 5 organizations by job count
        top_orgs = db.session.query(
            JobVacancy.organization,
            func.count(JobVacancy.id).label('count')
        ).filter(
            JobVacancy.status == 'active'
        ).group_by(
            JobVacancy.organization
        ).order_by(
            func.count(JobVacancy.id).desc()
        ).limit(5).all()

        # 6. Applications by status
        apps_by_status = db.session.query(
            UserJobApplication.status,
            func.count(UserJobApplication.id).label('count')
        ).group_by(UserJobApplication.status).all()

        # 7. Notifications sent in last 7 days
        last_7_days = datetime.now(timezone.utc) - timedelta(days=7)
        notifications_sent = db.session.query(
            func.count(Notification.id)
        ).filter(Notification.created_at >= last_7_days).scalar()

        # 8. Unread notification count across all users
        unread_notifications = db.session.query(
            func.count(Notification.id)
        ).filter(Notification.is_read.is_(False)).scalar()

        analytics = {
            'period_days': days,
            'jobs': {
                'by_type': [{'type': r.job_type, 'count': r.count} for r in job_by_type],
                'by_status': [{'status': r.status, 'count': r.count} for r in job_by_status],
                'daily_trend': [
                    {'date': r.day.date().isoformat(), 'count': r.count}
                    for r in jobs_per_day
                ],
            },
            'users': {
                'daily_registrations': [
                    {'date': r.day.date().isoformat(), 'count': r.count}
                    for r in users_per_day
                ],
            },
            'top_organizations': [
                {'organization': r.organization, 'job_count': r.count}
                for r in top_orgs
            ],
            'applications': {
                'by_status': [{'status': r.status, 'count': r.count} for r in apps_by_status],
            },
            'notifications': {
                'sent_last_7_days': notifications_sent,
                'total_unread': unread_notifications,
            },
        }

        return _ok({'analytics': analytics})

    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("Analytics query failed: %s", exc, exc_info=True)
        return _err(ErrorCode.SERVER_ERROR, 'Failed to retrieve analytics', 500)
