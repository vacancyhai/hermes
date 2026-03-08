"""
Celery application instance.

init_celery(app) must be called from the Flask app factory so that every
task runs inside a Flask application context and can safely use db.session,
current_app, and other Flask-bound resources.
"""
from celery import Celery
from celery.schedules import crontab as _crontab
import os

celery_app = Celery(
    'hermes',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/1'),
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone=os.getenv('CELERY_TIMEZONE', 'UTC'),
    enable_utc=True,
    task_track_started=True,
    # Celery Beat periodic schedule
    beat_schedule={
        # Deadline reminders — daily at 08:00 UTC
        'send-deadline-reminders-daily': {
            'task': 'reminder_tasks.send_deadline_reminders',
            'schedule': _crontab(hour=8, minute=0),
        },
        # Cleanup tasks — daily at 02:00 UTC
        'purge-expired-notifications-daily': {
            'task': 'cleanup_tasks.purge_expired_notifications',
            'schedule': _crontab(hour=2, minute=0),
        },
        'purge-expired-admin-logs-daily': {
            'task': 'cleanup_tasks.purge_expired_admin_logs',
            'schedule': _crontab(hour=2, minute=15),
        },
        'purge-soft-deleted-jobs-daily': {
            'task': 'cleanup_tasks.purge_soft_deleted_jobs',
            'schedule': _crontab(hour=2, minute=30),
        },
        'close-expired-job-listings-daily': {
            'task': 'cleanup_tasks.close_expired_job_listings',
            'schedule': _crontab(hour=1, minute=0),
        },
        # View-count flush — every 5 minutes
        'flush-job-views-every-5-minutes': {
            'task': 'views_flush_task.flush_job_views',
            'schedule': 300,  # seconds
        },
    },
)


def init_celery(app):
    """
    Wrap every Celery task so it executes inside a Flask application context.

    Call this once from create_app() after the Flask app is fully configured.
    Without this, tasks that access db.session or current_app will raise
    "RuntimeError: Working outside of application context."
    """
    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask
    return celery_app
