"""Notification-related Celery tasks."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, text

from app.celery_app import celery
from app.database import sync_engine
from sqlalchemy.orm import Session


@celery.task(name="app.tasks.notifications.send_deadline_reminders")
def send_deadline_reminders():
    """Send email reminders at T-7, T-3, T-1 days before application_end.
    Runs daily at 08:00 UTC via Beat schedule.
    TODO: Implement email sending.
    """
    pass


@celery.task(name="app.tasks.notifications.send_new_job_notifications")
def send_new_job_notifications(job_id: str):
    """Match a new active job to user profiles via org follows, then create notifications.

    Triggered when admin approves a job (draft → active).
    """
    with Session(sync_engine) as session:
        # Get the job
        row = session.execute(
            text("SELECT id, job_title, slug, organization FROM job_vacancies WHERE id = :jid"),
            {"jid": job_id},
        ).fetchone()
        if not row:
            return

        job_title = row[1]
        job_slug = row[2]
        org = row[3]

        # Find users following this organization (case-insensitive JSONB array search)
        profiles = session.execute(
            text("""
                SELECT up.user_id
                FROM user_profiles up
                WHERE EXISTS (
                    SELECT 1 FROM jsonb_array_elements_text(up.followed_organizations) AS elem
                    WHERE lower(elem) = lower(:org)
                )
            """),
            {"org": org},
        ).fetchall()

        if not profiles:
            return

        now = datetime.now(timezone.utc)
        for (user_id,) in profiles:
            session.execute(
                text("""
                    INSERT INTO notifications (id, user_id, entity_type, entity_id, type, title, message, action_url, created_at)
                    VALUES (:id, :uid, 'job', :jid, 'new_job_from_followed_org', :title, :msg, :url, :now)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "uid": str(user_id),
                    "jid": job_id,
                    "title": f"New job from {org}",
                    "msg": f"{job_title} has been posted by {org}.",
                    "url": f"/jobs/{job_slug}",
                    "now": now,
                },
            )

        session.commit()


@celery.task(name="app.tasks.notifications.notify_priority_subscribers")
def notify_priority_subscribers(job_id: str):
    """Notify users who marked a job as priority when it's updated.
    Triggered on admin job update (event-triggered).
    TODO: Implement.
    """
    pass
