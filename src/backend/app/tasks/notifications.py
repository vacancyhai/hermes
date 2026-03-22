"""Notification-related Celery tasks.

send_deadline_reminders     — Daily Beat task: T-7, T-3, T-1 deadline reminders
send_new_job_notifications  — Event: notify org followers on job approve
send_email_notification     — Sync email via SMTP (retries 3x)
send_push_notification      — FCM push (retries 3x, graceful no-op if unconfigured)
notify_priority_subscribers — Event: notify priority trackers on job update
"""

import os
import smtplib
import uuid
from datetime import date, datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import structlog
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.celery_app import celery
from app.config import settings
from app.database import sync_engine

logger = structlog.get_logger()

REMINDER_DAYS = [7, 3, 1]  # T-7, T-3, T-1
MAX_FCM_TOKENS = 10
BASE_URL = os.environ.get("FRONTEND_URL", "http://localhost:8080")

# Jinja2 env for email templates
_template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
_jinja_env = Environment(loader=FileSystemLoader(_template_dir), autoescape=True)


def _render_email(template_name: str, context: dict) -> str:
    """Render a Jinja2 email template to HTML string."""
    context.setdefault("base_url", BASE_URL)
    template = _jinja_env.get_template(f"email/{template_name}")
    return template.render(**context)


def _send_smtp(to: str, subject: str, html_body: str) -> bool:
    """Send an email via SMTP. Returns True on success."""
    if not settings.MAIL_ENABLED:
        logger.info("email_skipped", reason="MAIL_ENABLED=false", to=to, subject=subject)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.MAIL_DEFAULT_SENDER
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))

    try:
        if settings.MAIL_USE_TLS:
            server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT, timeout=30)
            server.starttls()
        else:
            server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT, timeout=30)

        if settings.MAIL_USERNAME:
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)

        server.sendmail(settings.MAIL_DEFAULT_SENDER, to, msg.as_string())
        server.quit()
        logger.info("email_sent", to=to, subject=subject)
        return True
    except Exception as exc:
        logger.error("email_failed", to=to, subject=subject, error=str(exc))
        raise


@celery.task(
    name="app.tasks.notifications.send_email_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def send_email_notification(self, to: str, subject: str, template_name: str, context: dict):
    """Send a templated email. Retries 3x with exponential backoff."""
    try:
        html = _render_email(template_name, context)
        _send_smtp(to, subject, html)
    except Exception as exc:
        countdown = 2 ** self.request.retries * 30
        logger.warning("email_retry", to=to, subject=subject, retry=self.request.retries, countdown=countdown)
        raise self.retry(exc=exc, countdown=countdown)


@celery.task(name="app.tasks.notifications.send_deadline_reminders")
def send_deadline_reminders():
    """Create in-app notifications at T-7, T-3, T-1 days before application_end.

    Runs daily at 08:00 UTC via Beat schedule.
    Only notifies users who have tracked the job and haven't withdrawn.
    Also sends email if user has email notifications enabled.
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

                sent_via = ["in_app"]

                session.execute(
                    text("""
                        INSERT INTO notifications (id, user_id, entity_type, entity_id, type, title, message, action_url, priority, sent_via, created_at)
                        VALUES (:id, :uid, 'job', :jid, :ntype, :title, :msg, :url, :priority, :sent_via, :now)
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
                        "sent_via": sent_via,
                        "now": now,
                    },
                )

                # Queue email if user has email notifications enabled
                _queue_email_for_user(
                    session, str(user_id),
                    subject=title,
                    template_name="deadline_reminder.html",
                    context={
                        "title": title,
                        "message": msg,
                        "job_title": job_title,
                        "organization": org,
                        "slug": slug,
                        "deadline": str(app_end),
                    },
                )

        session.commit()


@celery.task(name="app.tasks.notifications.send_new_job_notifications")
def send_new_job_notifications(job_id: str):
    """Match a new active job to user profiles via org follows, then create notifications.

    Triggered when admin approves a job (draft → active).
    Also sends email to followers with email notifications enabled.
    """
    with Session(sync_engine) as session:
        # Get the job
        row = session.execute(
            text("SELECT id, job_title, slug, organization, application_end FROM job_vacancies WHERE id = :jid"),
            {"jid": job_id},
        ).fetchone()
        if not row:
            return

        job_title = row[1]
        job_slug = row[2]
        org = row[3]
        app_end = row[4]

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
            sent_via = ["in_app"]

            session.execute(
                text("""
                    INSERT INTO notifications (id, user_id, entity_type, entity_id, type, title, message, action_url, sent_via, created_at)
                    VALUES (:id, :uid, 'job', :jid, 'new_job_from_followed_org', :title, :msg, :url, :sent_via, :now)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "uid": str(user_id),
                    "jid": job_id,
                    "title": f"New job from {org}",
                    "msg": f"{job_title} has been posted by {org}.",
                    "url": f"/jobs/{job_slug}",
                    "sent_via": sent_via,
                    "now": now,
                },
            )

            # Queue email if user has email notifications enabled
            _queue_email_for_user(
                session, str(user_id),
                subject=f"New job from {org}: {job_title}",
                template_name="new_job_alert.html",
                context={
                    "job_title": job_title,
                    "organization": org,
                    "slug": job_slug,
                    "deadline": str(app_end) if app_end else None,
                },
            )

        session.commit()


@celery.task(
    name="app.tasks.notifications.send_push_notification",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def send_push_notification(self, user_id: str, title: str, body: str, data: dict | None = None):
    """Send push notification via FCM. Graceful no-op if Firebase not configured."""
    if not settings.FIREBASE_CREDENTIALS_PATH:
        logger.info("push_skipped", reason="FIREBASE_CREDENTIALS_PATH not set", user_id=user_id)
        return

    try:
        import firebase_admin
        from firebase_admin import credentials, messaging

        # Initialize Firebase app (once)
        if not firebase_admin._apps:
            cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)

        # Get user's FCM tokens
        with Session(sync_engine) as session:
            row = session.execute(
                text("SELECT fcm_tokens FROM user_profiles WHERE user_id = :uid"),
                {"uid": user_id},
            ).fetchone()

            if not row or not row[0]:
                logger.info("push_skipped", reason="no_fcm_tokens", user_id=user_id)
                return

            # Check notification preferences
            prefs_row = session.execute(
                text("SELECT notification_preferences FROM user_profiles WHERE user_id = :uid"),
                {"uid": user_id},
            ).fetchone()
            prefs = prefs_row[0] if prefs_row and prefs_row[0] else {}
            if prefs.get("push") is False:
                logger.info("push_skipped", reason="push_disabled", user_id=user_id)
                return

            tokens = [t["token"] for t in row[0] if isinstance(t, dict) and "token" in t]
            if not tokens:
                return

            message = messaging.MulticastMessage(
                notification=messaging.Notification(title=title, body=body),
                data=data or {},
                tokens=tokens,
            )
            response = messaging.send_each_for_multicast(message)

            # Clean up invalid tokens
            invalid_tokens = []
            for idx, send_response in enumerate(response.responses):
                if send_response.exception and hasattr(send_response.exception, "code"):
                    if send_response.exception.code in ("NOT_FOUND", "UNREGISTERED"):
                        invalid_tokens.append(tokens[idx])

            if invalid_tokens:
                current_tokens = row[0]
                cleaned = [t for t in current_tokens if t.get("token") not in invalid_tokens]
                session.execute(
                    text("UPDATE user_profiles SET fcm_tokens = :tokens::jsonb WHERE user_id = :uid"),
                    {"tokens": str(cleaned).replace("'", '"'), "uid": user_id},
                )
                session.commit()
                logger.info("push_tokens_cleaned", user_id=user_id, removed=len(invalid_tokens))

            logger.info("push_sent", user_id=user_id, success=response.success_count, failure=response.failure_count)

    except Exception as exc:
        countdown = 2 ** self.request.retries * 30
        logger.error("push_failed", user_id=user_id, error=str(exc), retry=self.request.retries)
        raise self.retry(exc=exc, countdown=countdown)


@celery.task(name="app.tasks.notifications.notify_priority_subscribers")
def notify_priority_subscribers(job_id: str):
    """Notify users who marked a job as priority when it's updated.
    Triggered on admin job update (event-triggered).
    """
    with Session(sync_engine) as session:
        # Get job details
        job_row = session.execute(
            text("SELECT id, job_title, slug, organization FROM job_vacancies WHERE id = :jid"),
            {"jid": job_id},
        ).fetchone()
        if not job_row:
            return

        job_title = job_row[1]
        job_slug = job_row[2]
        org = job_row[3]

        # Find users with priority tracking for this job
        apps = session.execute(
            text("""
                SELECT user_id FROM user_job_applications
                WHERE job_id = :jid AND is_priority = true
                  AND status NOT IN ('rejected', 'selected', 'waiting_list')
            """),
            {"jid": job_id},
        ).fetchall()

        if not apps:
            return

        now = datetime.now(timezone.utc)
        for (user_id,) in apps:
            session.execute(
                text("""
                    INSERT INTO notifications (id, user_id, entity_type, entity_id, type, title, message, action_url, priority, sent_via, created_at)
                    VALUES (:id, :uid, 'job', :jid, 'priority_job_update', :title, :msg, :url, 'high', '{in_app}', :now)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "uid": str(user_id),
                    "jid": job_id,
                    "title": f"Update: {job_title}",
                    "msg": f"A priority job you're tracking ({job_title} by {org}) has been updated.",
                    "url": f"/jobs/{job_slug}",
                    "now": now,
                },
            )

        session.commit()
        logger.info("priority_notifications_sent", job_id=job_id, count=len(apps))


def _queue_email_for_user(session, user_id: str, subject: str, template_name: str, context: dict):
    """Check user's email preference and queue email task if enabled."""
    row = session.execute(
        text("""
            SELECT u.email, u.full_name, up.notification_preferences
            FROM users u
            LEFT JOIN user_profiles up ON up.user_id = u.id
            WHERE u.id = :uid
        """),
        {"uid": user_id},
    ).fetchone()

    if not row:
        return

    email, full_name, prefs = row
    prefs = prefs or {}

    # Default: email enabled unless explicitly disabled
    if prefs.get("email") is False:
        return

    context["name"] = full_name or email
    send_email_notification.delay(email, subject, template_name, context)
