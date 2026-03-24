"""Notification-related Celery tasks.

smart_notify                — Unified entry: routes to in-app + FCM + email + WhatsApp via NotificationService
send_deadline_reminders     — Daily Beat task: T-7, T-3, T-1 deadline reminders → delegates to smart_notify
send_new_job_notifications  — Event: notify org followers on job approve → delegates to smart_notify
send_email_notification     — Sync email via SMTP (retries 3x)
notify_priority_subscribers — Event: notify priority trackers on job update → delegates to smart_notify
"""

import json
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
BASE_URL = settings.FRONTEND_URL

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


def _get_sync_redis():
    """Return a synchronous Redis client for Celery tasks."""
    import redis
    return redis.from_url(settings.REDIS_URL, decode_responses=True)


# ─── Email Task (used by NotificationService) ──────────────────────────────


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


# ─── Smart Notify — unified entry point ─────────────────────────────────────


@celery.task(name="app.tasks.notifications.smart_notify")
def smart_notify(
    user_id: str,
    title: str,
    message: str,
    notification_type: str,
    priority: str = "medium",
    entity_type: str | None = None,
    entity_id: str | None = None,
    action_url: str | None = None,
    email_template: str | None = None,
    email_context: dict | None = None,
    delivery_mode: str = "staggered",
):
    """Unified notification entry point.

    delivery_mode:
      "instant"   — all 4 channels at T+0 (OTP, auth, welcome)
      "staggered" — in-app + push T+0, email T+15min, whatsapp T+1hr

    All channels always deliver — staggered just adds a time gap.
    """
    from app.services.notifications import NotificationService

    redis_client = _get_sync_redis()

    with Session(sync_engine) as session:
        svc = NotificationService(session, redis_sync=redis_client)
        notification_id = svc.send(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            entity_type=entity_type,
            entity_id=entity_id,
            action_url=action_url,
            email_template=email_template,
            email_context=email_context,
            delivery_mode=delivery_mode,
        )
    logger.info("smart_notify_complete", notification_id=notification_id, user_id=user_id, mode=delivery_mode)


@celery.task(name="app.tasks.notifications.deliver_delayed_email")
def deliver_delayed_email(notification_id: str, user_id: str, subject: str, template_name: str, context: dict):
    """Delayed email delivery for staggered mode. Fired T+15min after smart_notify."""
    from app.services.notifications import NotificationService

    redis_client = _get_sync_redis()
    now = datetime.now(timezone.utc)

    with Session(sync_engine) as session:
        svc = NotificationService(session, redis_sync=redis_client)
        svc._send_email(notification_id, user_id, subject, template_name, context, now)
        session.commit()
    logger.info("delayed_email_sent", notification_id=notification_id, user_id=user_id)


@celery.task(name="app.tasks.notifications.deliver_delayed_whatsapp")
def deliver_delayed_whatsapp(notification_id: str, user_id: str, title: str, message: str):
    """Delayed WhatsApp delivery for staggered mode. Fired T+1hr after smart_notify."""
    from app.services.notifications import NotificationService

    redis_client = _get_sync_redis()
    now = datetime.now(timezone.utc)

    with Session(sync_engine) as session:
        svc = NotificationService(session, redis_sync=redis_client)
        svc._send_whatsapp(notification_id, user_id, title, message, now)
        session.commit()
    logger.info("delayed_whatsapp_sent", notification_id=notification_id, user_id=user_id)


# ─── Deadline Reminders (Beat schedule) ──────────────────────────────────────


@celery.task(name="app.tasks.notifications.send_deadline_reminders")
def send_deadline_reminders():
    """Create notifications at T-7, T-3, T-1 days before application_end.

    Runs daily at 08:00 UTC via Beat schedule.
    Delegates to smart_notify for multi-channel delivery.
    """
    today = date.today()

    with Session(sync_engine) as session:
        for days_before in REMINDER_DAYS:
            target_date = today + timedelta(days=days_before)

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

                # Skip if reminder already sent
                existing = session.execute(
                    text("""
                        SELECT 1 FROM notifications
                        WHERE user_id = :uid AND entity_id = :jid AND type = :ntype
                        LIMIT 1
                    """),
                    {"uid": str(user_id), "jid": str(job_id), "ntype": f"deadline_reminder_{days_before}d"},
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

                smart_notify.delay(
                    user_id=str(user_id),
                    title=title,
                    message=msg,
                    notification_type=f"deadline_reminder_{days_before}d",
                    priority=priority,
                    entity_type="job",
                    entity_id=str(job_id),
                    action_url=f"/jobs/{slug}",
                    email_template="deadline_reminder.html",
                    email_context={
                        "title": title,
                        "message": msg,
                        "job_title": job_title,
                        "organization": org,
                        "slug": slug,
                        "deadline": str(app_end),
                    },
                )


# ─── New Job Notifications (event-triggered) ─────────────────────────────────


@celery.task(name="app.tasks.notifications.send_new_job_notifications")
def send_new_job_notifications(job_id: str):
    """Notify org followers when a job is approved (draft → active).

    Delegates to smart_notify for multi-channel delivery.
    """
    with Session(sync_engine) as session:
        row = session.execute(
            text("SELECT id, job_title, slug, organization, application_end FROM job_vacancies WHERE id = :jid"),
            {"jid": job_id},
        ).fetchone()
        if not row:
            return

        job_title, job_slug, org, app_end = row[1], row[2], row[3], row[4]

        profiles = session.execute(
            text("""
                SELECT up.user_id FROM user_profiles up
                WHERE EXISTS (
                    SELECT 1 FROM jsonb_array_elements_text(up.followed_organizations) AS elem
                    WHERE lower(elem) = lower(:org)
                )
            """),
            {"org": org},
        ).fetchall()

        if not profiles:
            return

        for (user_id,) in profiles:
            smart_notify.delay(
                user_id=str(user_id),
                title=f"New job from {org}",
                message=f"{job_title} has been posted by {org}.",
                notification_type="new_job_from_followed_org",
                priority="medium",
                entity_type="job",
                entity_id=job_id,
                action_url=f"/jobs/{job_slug}",
                email_template="new_job_alert.html",
                email_context={
                    "job_title": job_title,
                    "organization": org,
                    "slug": job_slug,
                    "deadline": str(app_end) if app_end else None,
                },
            )


# ─── Priority Subscribers (event-triggered) ───────────────────────────────────


@celery.task(name="app.tasks.notifications.notify_priority_subscribers")
def notify_priority_subscribers(job_id: str):
    """Notify users who marked a job as priority when it's updated.

    Delegates to smart_notify for multi-channel delivery.
    """
    with Session(sync_engine) as session:
        job_row = session.execute(
            text("SELECT id, job_title, slug, organization FROM job_vacancies WHERE id = :jid"),
            {"jid": job_id},
        ).fetchone()
        if not job_row:
            return

        job_title, job_slug, org = job_row[1], job_row[2], job_row[3]

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

        for (user_id,) in apps:
            smart_notify.delay(
                user_id=str(user_id),
                title=f"Update: {job_title}",
                message=f"A priority job you're tracking ({job_title} by {org}) has been updated.",
                notification_type="priority_job_update",
                priority="high",
                entity_type="job",
                entity_id=job_id,
                action_url=f"/jobs/{job_slug}",
            )

        logger.info("priority_notifications_queued", job_id=job_id, count=len(apps))


# ─── Legacy helper (kept for any direct callers) ─────────────────────────────


def _queue_email_for_user(session, user_id: str, subject: str, template_name: str, context: dict):
    """Check user's email preference and queue email task if enabled.

    Legacy helper — new code uses NotificationService._send_email instead.
    """
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
    if not email:
        return
    prefs = prefs or {}

    if prefs.get("email") is False:
        return

    context["name"] = full_name or email
    send_email_notification.delay(email, subject, template_name, context)
