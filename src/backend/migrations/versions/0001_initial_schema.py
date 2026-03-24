"""Consolidated initial schema — all 9 application tables.

Revision ID: 0001
Revises: None
Create Date: 2026-03-24

Merged from migrations 0001\u20130011. Represents the complete, final schema for a
fresh install. Existing databases that ran the incremental migrations must
stamp to this revision before running further migrations:

    docker compose exec backend alembic stamp 0001

Tables created (in FK-dependency order):
  1. users
  2. admin_users
  3. user_profiles
  4. job_vacancies
  5. user_job_applications
  6. notifications
  7. admin_logs
  8. user_devices
  9. notification_delivery_log

Notable design decisions:
  - google_id column never created (was added in 0008, dropped in 0011)
  - ck_notifications_entity_type constraint not created (dropped in 0011)
  - job expiry status is 'expired'; 'cancelled' is for manual soft-deletes only
  - FCM push tokens stored in user_profiles.fcm_tokens (not user_devices)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, INET, JSONB, UUID

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─── 1. users ────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=True),         # nullable: phone-only users
        sa.Column("password_hash", sa.String(255), nullable=True),              # nullable: Firebase handles auth
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20)),
        sa.Column("firebase_uid", sa.String(128), unique=True),
        sa.Column("migration_status", sa.String(20), nullable=False, server_default="native"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("is_email_verified", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("last_login", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('active','suspended','deleted')", name="ck_users_status"),
    )
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_status", "users", ["status"])
    op.create_index("ix_users_firebase_uid", "users", ["firebase_uid"], unique=True)

    # ─── 2. admin_users ──────────────────────────────────────────────────────
    op.create_table(
        "admin_users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20)),
        sa.Column("role", sa.String(20), nullable=False, server_default="operator"),
        sa.Column("department", sa.String(255)),
        sa.Column("permissions", JSONB, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("is_email_verified", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("last_login", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('admin','operator')", name="ck_admin_users_role"),
        sa.CheckConstraint("status IN ('active','suspended','deleted')", name="ck_admin_users_status"),
    )
    op.create_index("idx_admin_users_email", "admin_users", ["email"])
    op.create_index("idx_admin_users_status", "admin_users", ["status"])

    # ─── 3. user_profiles ────────────────────────────────────────────────────
    op.create_table(
        "user_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date_of_birth", sa.Date),
        sa.Column("gender", sa.String(20)),
        sa.Column("category", sa.String(20)),
        sa.Column("is_pwd", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("is_ex_serviceman", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("state", sa.String(100)),
        sa.Column("city", sa.String(100)),
        sa.Column("pincode", sa.String(10)),
        sa.Column("highest_qualification", sa.String(50)),
        sa.Column("education", JSONB, nullable=False, server_default="{}"),
        sa.Column("notification_preferences", JSONB, nullable=False, server_default="{}"),
        sa.Column("preferred_states", JSONB, nullable=False, server_default="[]"),
        sa.Column("preferred_categories", JSONB, nullable=False, server_default="[]"),
        sa.Column("followed_organizations", JSONB, nullable=False, server_default="[]"),
        sa.Column("fcm_tokens", JSONB, nullable=False, server_default="[]"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("gender IN ('Male','Female','Other')", name="ck_profiles_gender"),
        sa.CheckConstraint("category IN ('General','OBC','SC','ST','EWS','EBC')", name="ck_profiles_category"),
    )
    op.create_index("idx_user_profiles_user_id", "user_profiles", ["user_id"], unique=True)
    op.create_index("idx_user_profiles_education", "user_profiles", ["education"], postgresql_using="gin")
    op.create_index("idx_user_profiles_notif_prefs", "user_profiles", ["notification_preferences"], postgresql_using="gin")

    # ─── 4. job_vacancies ────────────────────────────────────────────────────
    op.create_table(
        "job_vacancies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_title", sa.String(500), nullable=False),
        sa.Column("slug", sa.String(500), unique=True, nullable=False),
        sa.Column("organization", sa.String(255), nullable=False),
        sa.Column("department", sa.String(255)),
        sa.Column("job_type", sa.String(50), nullable=False, server_default="latest_job"),
        sa.Column("employment_type", sa.String(50), server_default="permanent"),
        sa.Column("qualification_level", sa.String(50)),
        sa.Column("total_vacancies", sa.Integer),
        sa.Column("vacancy_breakdown", JSONB, nullable=False, server_default="{}"),
        sa.Column("description", sa.Text),
        sa.Column("short_description", sa.Text),
        sa.Column("eligibility", JSONB, nullable=False, server_default="{}"),
        sa.Column("application_details", JSONB, nullable=False, server_default="{}"),
        sa.Column("documents", JSONB, nullable=False, server_default="[]"),
        sa.Column("source_url", sa.Text),
        sa.Column("notification_date", sa.Date),
        sa.Column("application_start", sa.Date),
        sa.Column("application_end", sa.Date),
        sa.Column("exam_start", sa.Date),
        sa.Column("exam_end", sa.Date),
        sa.Column("result_date", sa.Date),
        sa.Column("exam_details", JSONB, nullable=False, server_default="{}"),
        sa.Column("salary_initial", sa.Integer),
        sa.Column("salary_max", sa.Integer),
        sa.Column("salary", JSONB, nullable=False, server_default="{}"),
        sa.Column("selection_process", JSONB, nullable=False, server_default="[]"),
        sa.Column("fee_general", sa.Integer),
        sa.Column("fee_obc", sa.Integer),
        sa.Column("fee_sc_st", sa.Integer),
        sa.Column("fee_ews", sa.Integer),
        sa.Column("fee_female", sa.Integer),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("is_featured", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("is_urgent", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("views", sa.Integer, nullable=False, server_default="0"),
        sa.Column("applications_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("admin_users.id")),
        sa.Column("source", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("source_pdf_path", sa.Text),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "job_type IN ('latest_job','result','admit_card','answer_key')",
            name="ck_jobs_job_type",
        ),
        sa.CheckConstraint(
            "employment_type IN ('permanent','temporary','contract','apprentice')",
            name="ck_jobs_employment_type",
        ),
        sa.CheckConstraint(
            "status IN ('draft','active','expired','cancelled','upcoming')",
            name="ck_jobs_status",
        ),
        sa.CheckConstraint("source IN ('manual','pdf_upload')", name="ck_jobs_source"),
    )
    op.create_index("idx_jobs_organization", "job_vacancies", ["organization"])
    op.create_index("idx_jobs_status_created", "job_vacancies", ["status", sa.text("created_at DESC")])
    op.create_index("idx_jobs_qual_level", "job_vacancies", ["qualification_level"])
    op.create_index("idx_jobs_application_end", "job_vacancies", ["application_end"])
    op.create_index("idx_jobs_org_status", "job_vacancies", ["organization", "status", sa.text("created_at DESC")])
    op.create_index("idx_jobs_eligibility_gin", "job_vacancies", ["eligibility"], postgresql_using="gin")
    op.execute("""
        ALTER TABLE job_vacancies ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('english', coalesce(job_title, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(organization, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(description, '')), 'C')
        ) STORED
    """)
    op.execute("CREATE INDEX idx_jobs_search ON job_vacancies USING GIN (search_vector)")

    # ─── 5. user_job_applications ─────────────────────────────────────────────
    op.create_table(
        "user_job_applications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", UUID(as_uuid=True), sa.ForeignKey("job_vacancies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("application_number", sa.String(100)),
        sa.Column("is_priority", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("applied_on", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("status", sa.String(50), nullable=False, server_default="applied"),
        sa.Column("notes", sa.Text),
        sa.Column("reminders", JSONB, nullable=False, server_default="[]"),
        sa.Column("result_info", JSONB, nullable=False, server_default="{}"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "job_id"),
        sa.CheckConstraint(
            "status IN ('applied','admit_card_released','exam_completed','result_pending',"
            "'selected','rejected','waiting_list')",
            name="ck_applications_status",
        ),
    )
    op.create_index("idx_applications_user_job", "user_job_applications", ["user_id", "job_id"])
    op.create_index("idx_applications_user_applied", "user_job_applications", ["user_id", sa.text("applied_on DESC")])

    # ─── 6. notifications ────────────────────────────────────────────────────
    # NOTE: ck_notifications_entity_type constraint intentionally omitted —
    # it was present in the original schema but removed to allow new
    # notification categories without requiring a migration.
    op.create_table(
        "notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(50)),
        sa.Column("entity_id", UUID(as_uuid=True)),
        sa.Column("type", sa.String(60), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("action_url", sa.Text),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("sent_via", ARRAY(sa.String)),
        sa.Column("priority", sa.String(10), nullable=False, server_default="medium"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("read_at", sa.DateTime(timezone=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW() + INTERVAL '90 days'")),
        sa.CheckConstraint("priority IN ('low','medium','high')", name="ck_notifications_priority"),
    )
    op.create_index("idx_notifications_user_read", "notifications", ["user_id", "is_read"])
    op.create_index("idx_notifications_user_created", "notifications", ["user_id", sa.text("created_at DESC")])
    op.create_index("idx_notifications_expires", "notifications", ["expires_at"])

    # ─── 7. admin_logs ───────────────────────────────────────────────────────
    op.create_table(
        "admin_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("admin_id", UUID(as_uuid=True), sa.ForeignKey("admin_users.id"), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100)),
        sa.Column("resource_id", UUID(as_uuid=True)),
        sa.Column("details", sa.Text),
        sa.Column("changes", JSONB, nullable=False, server_default="{}"),
        sa.Column("ip_address", INET),
        sa.Column("user_agent", sa.Text),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW() + INTERVAL '30 days'")),
    )
    op.create_index("idx_admin_logs_admin_ts", "admin_logs", ["admin_id", sa.text("timestamp DESC")])
    op.create_index("idx_admin_logs_expires", "admin_logs", ["expires_at"])

    # ─── 8. user_devices ─────────────────────────────────────────────────────
    # NOTE: FCM push notifications read tokens from user_profiles.fcm_tokens,
    # not from this table. user_devices is reserved for future device
    # management (fingerprint dedup, device listing UI).
    op.create_table(
        "user_devices",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fcm_token", sa.String(500)),
        sa.Column("device_name", sa.String(255), nullable=False, server_default="Unknown"),
        sa.Column("device_type", sa.String(20), nullable=False, server_default="web"),
        sa.Column("device_fingerprint", sa.String(255)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("TRUE")),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("device_type IN ('web','pwa','android','ios')", name="ck_devices_device_type"),
    )
    op.create_index("idx_devices_user_id", "user_devices", ["user_id"])
    op.create_index(
        "idx_devices_fcm_token", "user_devices", ["fcm_token"],
        unique=True, postgresql_where=sa.text("fcm_token IS NOT NULL"),
    )
    op.create_index("idx_devices_fingerprint", "user_devices", ["user_id", "device_fingerprint"])

    # ─── 9. notification_delivery_log ────────────────────────────────────────
    op.create_table(
        "notification_delivery_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("notification_id", UUID(as_uuid=True),
                  sa.ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("device_id", UUID(as_uuid=True),
                  sa.ForeignKey("user_devices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("error_message", sa.Text),
        sa.Column("attempted_at", sa.DateTime(timezone=True)),
        sa.Column("delivered_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("channel IN ('in_app','push','email','whatsapp','telegram')", name="ck_delivery_channel"),
        sa.CheckConstraint(
            "status IN ('pending','sent','delivered','failed','skipped')",
            name="ck_delivery_status",
        ),
    )
    op.create_index("idx_delivery_notification", "notification_delivery_log", ["notification_id"])
    op.create_index("idx_delivery_user_channel", "notification_delivery_log", ["user_id", "channel"])

    # ─── 10. job_admit_cards ─────────────────────────────────────────
    op.create_table(
        "job_admit_cards",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", UUID(as_uuid=True), sa.ForeignKey("job_vacancies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("phase_number", sa.SmallInteger, nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("download_url", sa.Text, nullable=False),
        sa.Column("valid_from", sa.Date, nullable=True),
        sa.Column("valid_until", sa.Date, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_admit_cards_job", "job_admit_cards", ["job_id", "phase_number"])
    op.create_index("idx_admit_cards_pub", "job_admit_cards", ["published_at"])

    # ─── 11. job_answer_keys ─────────────────────────────────────────
    op.create_table(
        "job_answer_keys",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", UUID(as_uuid=True), sa.ForeignKey("job_vacancies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("phase_number", sa.SmallInteger, nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("answer_key_type", sa.String(20), nullable=False, server_default="provisional"),
        sa.Column("files", JSONB, nullable=False, server_default="[]"),
        sa.Column("objection_url", sa.Text, nullable=True),
        sa.Column("objection_deadline", sa.Date, nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("answer_key_type IN ('provisional','final')", name="ck_answer_key_type"),
    )
    op.create_index("idx_answer_keys_job", "job_answer_keys", ["job_id", "phase_number"])
    op.create_index("idx_answer_keys_type", "job_answer_keys", ["job_id", "answer_key_type"])

    # ─── 12. job_results ─────────────────────────────────────────────
    op.create_table(
        "job_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", UUID(as_uuid=True), sa.ForeignKey("job_vacancies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("phase_number", sa.SmallInteger, nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("result_type", sa.String(20), nullable=False),
        sa.Column("download_url", sa.Text, nullable=True),
        sa.Column("cutoff_marks", JSONB, nullable=True),
        sa.Column("total_qualified", sa.Integer, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "result_type IN ('shortlist','cutoff','merit_list','final')",
            name="ck_result_type",
        ),
    )
    op.create_index("idx_results_job", "job_results", ["job_id", "phase_number"])
    op.create_index("idx_results_pub", "job_results", ["published_at"])


def downgrade() -> None:
    op.drop_table("job_results")
    op.drop_table("job_answer_keys")
    op.drop_table("job_admit_cards")
    op.drop_table("notification_delivery_log")
    op.drop_table("user_devices")
    op.drop_table("admin_logs")
    op.drop_table("notifications")
    op.drop_table("user_job_applications")
    op.drop_table("job_vacancies")
    op.drop_table("user_profiles")
    op.drop_table("admin_users")
    op.drop_table("users")
