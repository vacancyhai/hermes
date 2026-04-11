"""Notification-related Celery tasks.

smart_notify                — Unified entry: routes to in-app + FCM + email + WhatsApp + Telegram
send_deadline_reminders     — Daily Beat task: T-7, T-3, T-1 deadline reminders for watched jobs + exams
notify_watchers_on_update   — Event: notify watchers when a job/admission is approved or updated
send_email_notification     — Sync email via SMTP (retries 3x)
deliver_delayed_telegram    — Delayed Telegram delivery for staggered mode (T+15min)
"""

import os
import smtplib
from datetime import date, datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import structlog
from app.celery_app import celery
from app.config import settings
from app.database import sync_engine
from jinja2 import Environment, FileSystemLoader
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = structlog.get_logger()

REMINDER_DAYS = [7, 3, 1]  # T-7, T-3, T-1
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
        logger.info(
            "email_skipped", reason="MAIL_ENABLED=false", to=to, subject=subject
        )
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.MAIL_DEFAULT_SENDER
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))

    server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT, timeout=30)
    try:
        if settings.MAIL_USE_TLS:
            server.starttls()
        if settings.MAIL_USERNAME:
            server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
        server.sendmail(settings.MAIL_DEFAULT_SENDER, to, msg.as_string())
        logger.info("email_sent", to=to, subject=subject)
        return True
    except Exception as exc:
        logger.error("email_failed", to=to, subject=subject, error=str(exc))
        raise
    finally:
        server.quit()


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
def send_email_notification(
    self, to: str, subject: str, template_name: str, context: dict
):
    """Send a templated email. Retries 3x with exponential backoff."""
    try:
        html = _render_email(template_name, context)
        _send_smtp(to, subject, html)
    except Exception as exc:
        countdown = 2**self.request.retries * 30
        logger.warning(
            "email_retry",
            to=to,
            subject=subject,
            retry=self.request.retries,
            countdown=countdown,
        )
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
    logger.info(
        "smart_notify_complete",
        notification_id=notification_id,
        user_id=user_id,
        mode=delivery_mode,
    )


@celery.task(name="app.tasks.notifications.deliver_delayed_email")
def deliver_delayed_email(
    notification_id: str, user_id: str, subject: str, template_name: str, context: dict
):
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
def deliver_delayed_whatsapp(
    notification_id: str, user_id: str, title: str, message: str
):
    """Delayed WhatsApp delivery for staggered mode. Fired T+1hr after smart_notify."""
    from app.services.notifications import NotificationService

    redis_client = _get_sync_redis()
    now = datetime.now(timezone.utc)

    with Session(sync_engine) as session:
        svc = NotificationService(session, redis_sync=redis_client)
        svc._send_whatsapp(notification_id, user_id, title, message, now)
        session.commit()
    logger.info(
        "delayed_whatsapp_sent", notification_id=notification_id, user_id=user_id
    )


@celery.task(name="app.tasks.notifications.deliver_delayed_telegram")
def deliver_delayed_telegram(
    notification_id: str, user_id: str, title: str, message: str
):
    """Delayed Telegram delivery for staggered mode. Fired T+15min after smart_notify."""
    from app.services.notifications import NotificationService

    redis_client = _get_sync_redis()
    now = datetime.now(timezone.utc)

    with Session(sync_engine) as session:
        svc = NotificationService(session, redis_sync=redis_client)
        svc._send_telegram(notification_id, user_id, title, message, now)
        session.commit()
    logger.info(
        "delayed_telegram_sent", notification_id=notification_id, user_id=user_id
    )


# ─── Deadline Reminders (Beat schedule) ──────────────────────────────────────


def _build_reminder_text(
    days_before: int, job_title: str, org: str
) -> tuple[str, str, str]:
    """Return (title, message, priority) for a deadline reminder."""
    if days_before == 1:
        return (
            f"Last day to apply: {job_title}",
            f"Application deadline for {job_title} ({org}) is tomorrow!",
            "high",
        )
    if days_before == 3:
        return (
            f"3 days left: {job_title}",
            f"Application deadline for {job_title} ({org}) is in 3 days.",
            "high",
        )
    return (
        f"1 week left: {job_title}",
        f"Application deadline for {job_title} ({org}) is in 7 days.",
        "medium",
    )


@celery.task(name="app.tasks.notifications.send_deadline_reminders")
def send_deadline_reminders():
    """Create notifications at T-7, T-3, T-1 days before application_end.

    Covers two groups:
      1. Users watching a job via user_watches
      2. Users watching an admission via user_watches

    Runs daily at 08:00 UTC via Beat schedule.
    Delegates to smart_notify for multi-channel delivery.
    """
    today = date.today()

    with Session(sync_engine) as session:
        for days_before in REMINDER_DAYS:
            target_date = today + timedelta(days=days_before)

            # ── 1. Watch-based job reminders ──────────────────────────────────
            watch_job_rows = session.execute(
                text(
                    """
                    SELECT uw.id, uw.user_id, jv.id, jv.job_title, jv.slug, jv.organization, jv.application_end
                    FROM user_watches uw
                    JOIN jobs jv ON jv.id = uw.entity_id
                    WHERE uw.entity_type = 'job'
                      AND jv.application_end = :target_date
                      AND jv.status = 'active'
                """
                ),
                {"target_date": target_date},
            ).fetchall()

            for (
                _watch_id,
                user_id,
                job_id,
                job_title,
                slug,
                org,
                app_end,
            ) in watch_job_rows:
                ntype = f"deadline_reminder_{days_before}d"
                existing = session.execute(
                    text(
                        "SELECT 1 FROM notifications WHERE user_id=:uid AND entity_id=:eid AND type=:t LIMIT 1"
                    ),
                    {"uid": str(user_id), "eid": str(job_id), "t": ntype},
                ).fetchone()
                if existing:
                    continue

                title, msg, priority = _build_reminder_text(days_before, job_title, org)
                smart_notify.delay(
                    user_id=str(user_id),
                    title=title,
                    message=msg,
                    notification_type=ntype,
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

            # ── 2. Watch-based admission reminders ─────────────────────────────────
            watch_exam_rows = session.execute(
                text(
                    """
                    SELECT uw.user_id, ee.id, ee.exam_name, ee.slug, ee.conducting_body, ee.application_end
                    FROM user_watches uw
                    JOIN admissions ee ON ee.id = uw.entity_id
                    WHERE uw.entity_type = 'exam'
                      AND ee.application_end = :target_date
                      AND ee.status != 'cancelled'
                """
                ),
                {"target_date": target_date},
            ).fetchall()

            for (
                user_id,
                admission_id,
                exam_name,
                slug,
                conducting_body,
                app_end,
            ) in watch_exam_rows:
                ntype = f"deadline_reminder_{days_before}d"
                existing = session.execute(
                    text(
                        "SELECT 1 FROM notifications WHERE user_id=:uid AND entity_id=:eid AND type=:t LIMIT 1"
                    ),
                    {"uid": str(user_id), "eid": str(admission_id), "t": ntype},
                ).fetchone()
                if existing:
                    continue

                title, msg, priority = _build_reminder_text(
                    days_before, exam_name, conducting_body
                )
                smart_notify.delay(
                    user_id=str(user_id),
                    title=title,
                    message=msg,
                    notification_type=ntype,
                    priority=priority,
                    entity_type="exam",
                    entity_id=str(admission_id),
                    action_url=f"/admissions/{slug}",
                    email_template="deadline_reminder.html",
                    email_context={
                        "title": title,
                        "message": msg,
                        "job_title": exam_name,
                        "organization": conducting_body,
                        "slug": slug,
                        "deadline": str(app_end),
                    },
                )


# ─── Watcher Notifications (event-triggered) ─────────────────────────────────


@celery.task(name="app.tasks.notifications.notify_watchers_on_update")
def notify_watchers_on_update(entity_type: str, entity_id: str):
    """Notify all users watching a job or admission when it is approved or updated.

    entity_type: 'job' | 'admission'
    Delegates to smart_notify for multi-channel delivery.
    """
    with Session(sync_engine) as session:
        if entity_type == "job":
            row = session.execute(
                text(
                    "SELECT job_title, slug, organization, application_end FROM jobs WHERE id = :eid"
                ),
                {"eid": entity_id},
            ).fetchone()
            if not row:
                return
            name, slug, org, _ = row
            action_url = f"/jobs/{slug}"
            title = f"Update: {name}"
            msg = f"{name} by {org} has been updated."
        else:
            row = session.execute(
                text(
                    "SELECT exam_name, slug, conducting_body, application_end FROM admissions WHERE id = :eid"
                ),
                {"eid": entity_id},
            ).fetchone()
            if not row:
                return
            name, slug, org, _ = row
            action_url = f"/admissions/{slug}"
            title = f"Update: {name}"
            msg = f"{name} by {org} has been updated."

        watchers = session.execute(
            text(
                "SELECT user_id FROM user_watches WHERE entity_type = :et AND entity_id = :eid"
            ),
            {"et": entity_type, "eid": entity_id},
        ).fetchall()

        if not watchers:
            return

        BATCH_SIZE = 100
        user_ids = [str(row[0]) for row in watchers]
        for i in range(0, len(user_ids), BATCH_SIZE):
            batch = user_ids[i : i + BATCH_SIZE]
            notify_watcher_batch.delay(
                user_ids=batch,
                title=title,
                message=msg,
                entity_type=entity_type,
                entity_id=entity_id,
                action_url=action_url,
            )

        logger.info(
            "watchers_notified",
            entity_type=entity_type,
            entity_id=entity_id,
            count=len(watchers),
        )


@celery.task(name="app.tasks.notifications.notify_watcher_batch")
def notify_watcher_batch(
    user_ids: list[str],
    title: str,
    message: str,
    entity_type: str,
    entity_id: str,
    action_url: str,
):
    """Process a batch of watcher notifications dispatched by notify_watchers_on_update."""
    for user_id in user_ids:
        smart_notify.delay(
            user_id=user_id,
            title=title,
            message=message,
            notification_type="watched_item_updated",
            priority="medium",
            entity_type=entity_type,
            entity_id=entity_id,
            action_url=action_url,
        )


@celery.task(name="app.tasks.notifications.send_new_job_notifications")
def send_new_job_notifications(job_id: str):
    """Notify users who follow the job's organization when a new job is posted."""
    pass


@celery.task(name="app.tasks.notifications.notify_priority_subscribers")
def notify_priority_subscribers(job_id: str):
    """Notify users who are priority-tracking a job when it gets updated."""
    pass
