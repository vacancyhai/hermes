"""Smart Notification Service — unified multi-channel delivery.

Two delivery modes:
  instant   — All 4 channels fire at T+0 (OTP, password reset, welcome)
  staggered — In-app + push at T+0, email at T+15min, WhatsApp at T+1hr

All channels always deliver (no read-checks, no skipping). The time gap
in staggered mode just avoids bombarding the user simultaneously.

User preferences (notification_preferences JSONB) respected per channel.
Every delivery attempt logged in notification_delivery_log.
"""

import json
import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings

logger = structlog.get_logger()

# OCI Email free tier daily limit (leave 10% headroom)
DAILY_EMAIL_LIMIT = 2700


class NotificationService:
    """Stateless service — runs inside Celery tasks (sync context)."""

    def __init__(self, session: Session, redis_sync=None):
        self.session = session
        self.redis = redis_sync

    # ─── Public API ─────────────────────────────────────────────────────

    def send(
        self,
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
    ) -> str:
        """Create notification and deliver to channels.

        delivery_mode:
          "instant"   — all 5 channels at T+0 (OTP, auth, welcome)
          "staggered" — in-app + push at T+0, email T+15min, whatsapp T+1hr,
                          telegram T+15min

        Returns the notification ID (str).
        """
        notification_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        # Load user preferences once
        prefs = self._load_preferences(user_id)

        # 1. In-app — always instant
        self._create_in_app(
            notification_id, user_id, title, message, notification_type,
            priority, entity_type, entity_id, action_url, now,
        )

        # 2. Push — always instant (FCM, fingerprint de-dup)
        if prefs.get("push") is not False:
            self._send_push(notification_id, user_id, title, message, now)

        # 3. Email
        if prefs.get("email") is not False and email_template:
            if delivery_mode == "instant":
                self._send_email(notification_id, user_id, title, email_template, email_context or {}, now)
            else:
                self._schedule_delayed_email(
                    notification_id, user_id, title, email_template, email_context or {},
                )

        # 4. WhatsApp
        if prefs.get("whatsapp") is not False:
            if delivery_mode == "instant":
                self._send_whatsapp(notification_id, user_id, title, message, now)
            else:
                self._schedule_delayed_whatsapp(notification_id, user_id, title, message)

        # 5. Telegram
        tg_prefs = prefs.get("telegram")
        tg_enabled = tg_prefs.get("enabled", True) if isinstance(tg_prefs, dict) else (tg_prefs is not False)
        if tg_enabled:
            if delivery_mode == "instant":
                self._send_telegram(notification_id, user_id, title, message, now)
            else:
                self._schedule_delayed_telegram(notification_id, user_id, title, message)

        self.session.commit()

        logger.info(
            "notification_sent",
            notification_id=notification_id,
            user_id=user_id,
            type=notification_type,
            priority=priority,
            delivery_mode=delivery_mode,
        )
        return notification_id

    # ─── 1. In-App ─────────────────────────────────────────────────────

    def _create_in_app(
        self, notification_id, user_id, title, message, notification_type,
        priority, entity_type, entity_id, action_url, now,
    ):
        self.session.execute(
            text("""
                INSERT INTO notifications
                    (id, user_id, entity_type, entity_id, type, title, message,
                     action_url, priority, sent_via, created_at)
                VALUES
                    (:id, :uid, :etype, :eid, :ntype, :title, :msg,
                     :url, :priority, :sent_via, :now)
            """),
            {
                "id": notification_id,
                "uid": user_id,
                "etype": entity_type,
                "eid": entity_id,
                "ntype": notification_type,
                "title": title,
                "msg": message,
                "url": action_url,
                "priority": priority,
                "sent_via": ["in_app"],
                "now": now,
            },
        )
        self._log_delivery(notification_id, user_id, "in_app", "delivered", now, delivered_at=now)

    # ─── 2. Push — FCM via user_profiles.fcm_tokens ─────────────────────

    def _send_push(self, notification_id, user_id, title, message, now):
        """Send FCM push to all registered devices, deduplicating by fingerprint."""
        rows = self.session.execute(
            text("""
                SELECT id, fcm_token, device_fingerprint, last_active_at
                FROM user_devices
                WHERE user_id = :uid AND is_active = true AND fcm_token IS NOT NULL
                ORDER BY last_active_at DESC
            """),
            {"uid": user_id},
        ).fetchall()

        if not rows:
            self._log_delivery(notification_id, user_id, "push", "skipped", now, error="no_devices")
            return

        sent_any = False
        seen_fingerprints: set[str] = set()

        for _device_id, fcm_token, fingerprint, _last_active in rows:
            if fingerprint and fingerprint in seen_fingerprints:
                continue
            if fingerprint:
                seen_fingerprints.add(fingerprint)
            success = self._send_fcm(fcm_token, title, message, notification_id)
            status = "sent" if success else "failed"
            self._log_delivery(notification_id, user_id, "push", status, now,
                               delivered_at=now if success else None)
            if success:
                sent_any = True

        if sent_any:
            self._append_sent_via(notification_id, "push")

    def _send_fcm(self, token: str, title: str, body: str, notification_id: str) -> bool:
        """Send a single FCM message. Returns True on success, False otherwise."""
        success, _ = self._send_fcm_with_status(token, title, body, notification_id)
        return success

    def _send_fcm_with_status(self, token: str, title: str, body: str, notification_id: str) -> tuple[bool, bool]:
        """Send a single FCM message. Returns (success, is_invalid_token)."""
        from app.firebase import init_firebase

        if not init_firebase():
            logger.info("fcm_skipped", reason="Firebase not configured")
            return False, False

        try:
            from firebase_admin import messaging

            msg = messaging.Message(
                notification=messaging.Notification(title=title, body=body),
                data={"notification_id": notification_id},
                token=token,
            )
            messaging.send(msg)
            logger.info("fcm_sent", token=token[:20] + "...")
            return True, False
        except Exception as exc:
            err_str = str(exc)
            is_invalid = any(code in err_str for code in ("NOT_FOUND", "UNREGISTERED", "INVALID_ARGUMENT"))
            logger.error("fcm_failed", error=err_str, token=token[:20] + "...")
            return False, is_invalid

    # ─── 3. Email ──────────────────────────────────────────────────────

    def _send_email(self, notification_id, user_id, subject, template_name, context, now):
        """Send email immediately (instant mode)."""
        if self._is_email_limit_reached():
            self._log_delivery(notification_id, user_id, "email", "skipped", now, error="daily_limit")
            return

        row = self.session.execute(
            text("SELECT email, full_name FROM users WHERE id = :uid"),
            {"uid": user_id},
        ).fetchone()
        if not row or not row[0]:
            self._log_delivery(notification_id, user_id, "email", "skipped", now, error="no_email")
            return

        email, full_name = row
        context["name"] = full_name or email

        from app.tasks.notifications import send_email_notification
        send_email_notification.delay(email, subject, template_name, context)

        self._log_delivery(notification_id, user_id, "email", "queued", now)
        self._append_sent_via(notification_id, "email")
        self._increment_email_count()

    def _schedule_delayed_email(self, notification_id, user_id, subject, template_name, context):
        """Schedule email after NOTIFY_EMAIL_DELAY seconds (staggered mode)."""
        from app.tasks.notifications import deliver_delayed_email
        deliver_delayed_email.apply_async(
            args=[notification_id, user_id, subject, template_name, context],
            countdown=settings.NOTIFY_EMAIL_DELAY,
        )

    def _is_email_limit_reached(self) -> bool:
        if not self.redis:
            return False
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        key = f"{settings.REDIS_KEY_PREFIX}:email_count:{today}"
        try:
            count = self.redis.get(key)
            return int(count) >= DAILY_EMAIL_LIMIT if count else False
        except Exception:
            return False

    def _increment_email_count(self):
        if not self.redis:
            return
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        key = f"{settings.REDIS_KEY_PREFIX}:email_count:{today}"
        try:
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, 90000)  # 25 hours
            pipe.execute()
        except Exception as exc:
            logger.warning("email_count_incr_failed", error=str(exc))

    # ─── 4. WhatsApp ──────────────────────────────────────────────────

    def _send_whatsapp(self, notification_id, user_id, title, message, now):
        """Send WhatsApp immediately (instant mode)."""
        row = self.session.execute(
            text("""
                SELECT up.notification_preferences, u.phone
                FROM user_profiles up
                JOIN users u ON u.id = up.user_id
                WHERE up.user_id = :uid
            """),
            {"uid": user_id},
        ).fetchone()

        if not row:
            self._log_delivery(notification_id, user_id, "whatsapp", "skipped", now, error="no_profile")
            return

        prefs, phone = row
        wa_config = (prefs or {}).get("whatsapp", {})
        wa_phone = wa_config.get("phone") or phone

        if not wa_phone:
            self._log_delivery(notification_id, user_id, "whatsapp", "skipped", now, error="no_phone")
            return

        success = self._send_whatsapp_message(wa_phone, title, message)
        status = "sent" if success else "failed"
        self._log_delivery(
            notification_id, user_id, "whatsapp", status, now,
            delivered_at=now if success else None,
            error=None if success else "send_failed",
        )
        if success:
            self._append_sent_via(notification_id, "whatsapp")

    def _schedule_delayed_whatsapp(self, notification_id, user_id, title, message):
        """Schedule WhatsApp after NOTIFY_WHATSAPP_DELAY seconds (staggered mode)."""
        from app.tasks.notifications import deliver_delayed_whatsapp
        deliver_delayed_whatsapp.apply_async(
            args=[notification_id, user_id, title, message],
            countdown=settings.NOTIFY_WHATSAPP_DELAY,
        )

    def _send_whatsapp_message(self, phone: str, title: str, message: str) -> bool:
        """Send via WhatsApp Cloud API. Placeholder until configured."""
        # TODO: Implement when WHATSAPP_API_TOKEN + WHATSAPP_PHONE_NUMBER_ID are in settings
        logger.info("whatsapp_not_configured", phone=phone[:6] + "***", title=title)
        return False

    # ─── 5. Telegram ───────────────────────────────────────────────

    def _send_telegram(self, notification_id, user_id, title, message, now):
        """Send Telegram message immediately (instant mode)."""
        row = self.session.execute(
            text("SELECT notification_preferences FROM user_profiles WHERE user_id = :uid"),
            {"uid": user_id},
        ).fetchone()

        if not row:
            self._log_delivery(notification_id, user_id, "telegram", "skipped", now, error="no_profile")
            return

        prefs = row[0] or {}
        tg_config = prefs.get("telegram", {})
        if not isinstance(tg_config, dict):
            self._log_delivery(notification_id, user_id, "telegram", "skipped", now, error="no_chat_id")
            return

        chat_id = tg_config.get("chat_id")
        if not chat_id:
            self._log_delivery(notification_id, user_id, "telegram", "skipped", now, error="no_chat_id")
            return

        success = self._send_telegram_message(chat_id, title, message)
        status = "sent" if success else "failed"
        self._log_delivery(
            notification_id, user_id, "telegram", status, now,
            delivered_at=now if success else None,
            error=None if success else "send_failed",
        )
        if success:
            self._append_sent_via(notification_id, "telegram")

    def _schedule_delayed_telegram(self, notification_id, user_id, title, message):
        """Schedule Telegram after NOTIFY_TELEGRAM_DELAY seconds (staggered mode)."""
        from app.tasks.notifications import deliver_delayed_telegram
        deliver_delayed_telegram.apply_async(
            args=[notification_id, user_id, title, message],
            countdown=settings.NOTIFY_TELEGRAM_DELAY,
        )

    def _send_telegram_message(self, chat_id: str, title: str, message: str) -> bool:
        """Send message via Telegram Bot API.

        Requires TELEGRAM_BOT_TOKEN to be set. Users must first start a
        conversation with the bot and save their chat_id via
        PUT /api/v1/users/me/notification-preferences {"telegram_chat_id": "..."}.
        """
        if not settings.TELEGRAM_BOT_TOKEN:
            logger.info("telegram_not_configured", chat_id=chat_id[:6] + "***")
            return False

        import json
        import urllib.request
        import urllib.error

        try:
            payload = json.dumps({
                "chat_id": chat_id,
                "text": f"*{title}*\n\n{message}",
                "parse_mode": "Markdown",
            }).encode()
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                data=payload,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                success = resp.status == 200
                logger.info("telegram_sent", chat_id=chat_id[:6] + "***")
                return success
        except urllib.error.HTTPError as exc:
            logger.error("telegram_failed", error=f"HTTP {exc.code}", chat_id=chat_id[:6] + "***")
            return False
        except Exception as exc:
            logger.error("telegram_failed", error=str(exc), chat_id=chat_id[:6] + "***")
            return False

    # ─── Helpers ───────────────────────────────────────────────────────

    def _load_preferences(self, user_id: str) -> dict:
        row = self.session.execute(
            text("SELECT notification_preferences FROM user_profiles WHERE user_id = :uid"),
            {"uid": user_id},
        ).fetchone()
        return (row[0] if row and row[0] else {}) or {}

    def _append_sent_via(self, notification_id: str, channel: str):
        self.session.execute(
            text("UPDATE notifications SET sent_via = sent_via || :ch WHERE id = :nid"),
            {"ch": "{" + channel + "}", "nid": notification_id},
        )

    def _log_delivery(
        self, notification_id, user_id, channel, status, now,
        delivered_at=None, device_id=None, error=None,
    ):
        self.session.execute(
            text("""
                INSERT INTO notification_delivery_log
                    (id, notification_id, user_id, channel, status, device_id,
                     error_message, attempted_at, delivered_at, created_at)
                VALUES
                    (:id, :nid, :uid, :channel, :status, :did,
                     :err, :now, :delivered, :now)
            """),
            {
                "id": str(uuid.uuid4()),
                "nid": notification_id,
                "uid": user_id,
                "channel": channel,
                "status": status,
                "did": device_id,
                "err": error,
                "now": now,
                "delivered": delivered_at,
            },
        )
