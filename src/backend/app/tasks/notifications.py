"""Notification-related Celery tasks."""

from app.celery_app import celery


@celery.task(name="app.tasks.notifications.send_deadline_reminders")
def send_deadline_reminders():
    """Send email reminders at T-7, T-3, T-1 days before application_end.
    Runs daily at 08:00 UTC via Beat schedule.
    TODO: Implement.
    """
    pass


@celery.task(name="app.tasks.notifications.send_new_job_notifications")
def send_new_job_notifications(job_id: str):
    """Match a new active job to user profiles and org follows, then notify.
    Triggered on new job creation (event-triggered, not Beat).
    TODO: Implement.
    """
    pass


@celery.task(name="app.tasks.notifications.notify_priority_subscribers")
def notify_priority_subscribers(job_id: str):
    """Notify users who marked a job as priority when it's updated.
    Triggered on admin job update (event-triggered).
    TODO: Implement.
    """
    pass
