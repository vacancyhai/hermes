"""Notification-related Celery tasks."""

import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select, text

from app.celery_app import celery
from app.database import sync_engine
from sqlalchemy.orm import Session

REMINDER_DAYS = [7, 3, 1]  # T-7, T-3, T-1


@celery.task(name="app.tasks.notifications.send_deadline_reminders")
def send_deadline_reminders():
    """Create in-app notifications at T-7, T-3, T-1 days before application_end.

    Runs daily at 08:00 UTC via Beat schedule.
    Only notifies users who have tracked the job and haven't withdrawn.
    """
    today = date.today()
    now = datetime.now(timezone.utc)

    with Session(sync_engine) as session:
        for days_before in REMINDER_DAYS:
            target_date = today + timedelta(days=days_before)

            # Find tracked applications where the job deadline matches target_date
            rows = session.execute(
                text("""
                    SELECT uja.id, uja.user_id, uja.job_id, jv.job_title, jv.slug, jv.organization, jv.application_end
                    FROM user_job_applications uja
                    JOIN job_vacancies jv ON jv.id = uja.job_id
                    WHERE jv.application_end = :target_date
                      AND jv.status = 'active'
                      AND uja.status NOT IN ('rejected', 'selected', 'waiting_list')
                """),
                {"target_date": target_date},
            ).fetchall()

            for row in rows:
                app_id, user_id, job_id, job_title, slug, org, app_end = row

                # Skip if reminder already sent for this (user, job, days_before) combo
                existing = session.execute(
                    text("""
                        SELECT 1 FROM notifications
                        WHERE user_id = :uid AND entity_id = :jid
                          AND type = :ntype
                        LIMIT 1
                    """),
                    {
                        "uid": str(user_id),
                        "jid": str(job_id),
                        "ntype": f"deadline_reminder_{days_before}d",
                    },
                ).fetchone()
                if existing:
                    continue

                if days_before == 1:
                    title = f"Last day to apply: {job_title}"
                    msg = f"Application deadline for {job_title} ({org}) is tomorrow!"
                    priority = "high"
                elif days_before == 3:
                    title = f"3 days left: {job_title}"
                    msg = f"Application deadline for {job_title} ({org}) is in 3 days."
                    priority = "high"
                else:
                    title = f"1 week left: {job_title}"
                    msg = f"Application deadline for {job_title} ({org}) is in 7 days."
                    priority = "medium"

                session.execute(
                    text("""
                        INSERT INTO notifications (id, user_id, entity_type, entity_id, type, title, message, action_url, priority, created_at)
                        VALUES (:id, :uid, 'job', :jid, :ntype, :title, :msg, :url, :priority, :now)
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "uid": str(user_id),
                        "jid": str(job_id),
                        "ntype": f"deadline_reminder_{days_before}d",
                        "title": title,
                        "msg": msg,
                        "url": f"/jobs/{slug}",
                        "priority": priority,
                        "now": now,
                    },
                )

        session.commit()


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
