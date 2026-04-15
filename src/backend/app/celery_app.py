"""Celery application configuration."""

from app.config import settings
from celery import Celery
from celery.schedules import crontab

celery = Celery(
    "hermes",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)

# Explicitly include task modules for reliable registration
celery.conf.update(
    include=[
        "app.tasks.notifications",
        "app.tasks.cleanup",
        "app.tasks.jobs",
        "app.tasks.seo",
    ],
)

# Beat schedule — matches DESIGN.md
celery.conf.beat_schedule = {
    "send-deadline-reminders": {
        "task": "app.tasks.notifications.send_deadline_reminders",
        "schedule": crontab(hour=8, minute=0),  # Daily 08:00 UTC
    },
    "purge-expired-notifications": {
        "task": "app.tasks.cleanup.purge_expired_notifications",
        "schedule": crontab(hour=1, minute=0),  # Daily 01:00 UTC
    },
    "purge-expired-admin-logs": {
        "task": "app.tasks.cleanup.purge_expired_admin_logs",
        "schedule": crontab(hour=1, minute=30),  # Daily 01:30 UTC
    },
    "purge-soft-deleted-jobs": {
        "task": "app.tasks.cleanup.purge_soft_deleted_jobs",
        "schedule": crontab(hour=2, minute=0),  # Daily 02:00 UTC
    },
    "close-expired-job-listings": {
        "task": "app.tasks.jobs.close_expired_job_listings",
        "schedule": crontab(hour=2, minute=30),  # Daily 02:30 UTC
    },
    "update-admission-statuses": {
        "task": "app.tasks.jobs.update_admission_statuses",
        "schedule": crontab(hour=2, minute=35),  # Daily 02:35 UTC
    },
    "generate-sitemap": {
        "task": "app.tasks.seo.generate_sitemap",
        "schedule": crontab(hour=4, minute=0),  # Daily 04:00 UTC
    },
}
