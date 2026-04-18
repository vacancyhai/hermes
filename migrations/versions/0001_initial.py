"""Complete initial schema — all tables for a fresh installation.

Revision ID: 0001_initial
Revises: None
Create Date: 2026-04-14

Tables (in dependency order):
  1.  users
  2.  admin_users
  3.  user_profiles
  4.  jobs
  5.  notifications
  6.  admin_logs
  7.  user_devices
  8.  notification_delivery_log
  9.  admissions
  10. admit_cards
  11. answer_keys
  12. results
  13. user_tracks
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. users ──────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("firebase_uid", sa.String(128), unique=True, nullable=True),
        sa.Column("migration_status", sa.String(20), nullable=False, server_default="native"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_phone_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("status IN ('active', 'suspended', 'deleted')", name="ck_users_status"),
    )
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_status", "users", ["status"])
    op.create_index("ix_users_firebase_uid", "users", ["firebase_uid"], unique=True)

    # ── 2. admin_users ────────────────────────────────────────────────────────
    op.create_table(
        "admin_users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("role", sa.String(20), nullable=False, server_default="operator"),
        sa.Column("department", sa.String(255), nullable=True),
        sa.Column("permissions", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("is_email_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("role IN ('admin', 'operator')", name="ck_admin_users_role"),
        sa.CheckConstraint("status IN ('active', 'suspended', 'deleted')", name="ck_admin_users_status"),
    )
    op.create_index("idx_admin_users_email", "admin_users", ["email"])
    op.create_index("idx_admin_users_status", "admin_users", ["status"])

    # ── 3. user_profiles ──────────────────────────────────────────────────────
    op.create_table(
        "user_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("gender", sa.String(20), nullable=True),
        sa.Column("category", sa.String(20), nullable=True),
        sa.Column("is_pwd", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_ex_serviceman", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("pincode", sa.String(10), nullable=True),
        sa.Column("highest_qualification", sa.String(50), nullable=True),
        sa.Column("education", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("notification_preferences", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("preferred_states", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("preferred_categories", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("fcm_tokens", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("followed_organizations", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("gender IN ('Male', 'Female', 'Other')", name="ck_profiles_gender"),
        sa.CheckConstraint("category IN ('General', 'OBC', 'SC', 'ST', 'EWS', 'EBC')", name="ck_profiles_category"),
        sa.UniqueConstraint("user_id", name="idx_user_profiles_user_id"),
    )
    op.execute("CREATE INDEX idx_user_profiles_education ON user_profiles USING GIN(education)")
    op.execute("CREATE INDEX idx_user_profiles_notif_prefs ON user_profiles USING GIN(notification_preferences)")

    # ── 4. jobs ───────────────────────────────────────────────────────────────
    op.create_table(
        "jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_title", sa.String(500), nullable=False),
        sa.Column("slug", sa.String(500), unique=True, nullable=False),
        sa.Column("organization", sa.String(255), nullable=False),
        sa.Column("department", sa.String(255), nullable=True),
        sa.Column("employment_type", sa.String(50), nullable=True, server_default="permanent"),
        sa.Column("qualification_level", sa.String(50), nullable=True),
        sa.Column("total_vacancies", sa.Integer(), nullable=True),
        sa.Column("vacancy_breakdown", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("short_description", sa.Text(), nullable=True),
        sa.Column("eligibility", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("application_details", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("documents", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("notification_date", sa.Date(), nullable=True),
        sa.Column("application_start", sa.Date(), nullable=True),
        sa.Column("application_end", sa.Date(), nullable=True),
        sa.Column("exam_start", sa.Date(), nullable=True),
        sa.Column("exam_end", sa.Date(), nullable=True),
        sa.Column("result_date", sa.Date(), nullable=True),
        sa.Column("exam_details", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("salary_initial", sa.Integer(), nullable=True),
        sa.Column("salary_max", sa.Integer(), nullable=True),
        sa.Column("links", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("salary", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("selection_process", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("fee_general", sa.Integer(), nullable=True),
        sa.Column("fee_obc", sa.Integer(), nullable=True),
        sa.Column("fee_sc_st", sa.Integer(), nullable=True),
        sa.Column("fee_ews", sa.Integer(), nullable=True),
        sa.Column("fee_female", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("admin_users.id"), nullable=True),
        sa.Column("source", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("source_pdf_path", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("employment_type IN ('permanent', 'temporary', 'contract', 'apprentice')", name="ck_jobs_employment_type"),
        sa.CheckConstraint("status IN ('upcoming', 'active', 'inactive', 'closed')", name="ck_jobs_status"),
        sa.CheckConstraint("source IN ('manual', 'pdf_upload')", name="ck_jobs_source"),
    )
    op.create_index("idx_jobs_organization", "jobs", ["organization"])
    op.create_index("idx_jobs_status_created", "jobs", ["status", sa.text("created_at DESC")])
    op.create_index("idx_jobs_qual_level", "jobs", ["qualification_level"])
    op.create_index("idx_jobs_application_end", "jobs", ["application_end"])
    op.create_index("idx_jobs_org_status", "jobs", ["organization", "status", sa.text("created_at DESC")])
    op.execute("CREATE INDEX idx_jobs_eligibility_gin ON jobs USING GIN(eligibility)")
    op.execute("""
        ALTER TABLE jobs ADD COLUMN search_vector tsvector
            GENERATED ALWAYS AS (
                setweight(to_tsvector('english', coalesce(job_title, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(organization, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(description, '')), 'C')
            ) STORED
    """)
    op.execute("CREATE INDEX idx_jobs_search ON jobs USING GIN(search_vector)")

    # ── 5. notifications ──────────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("type", sa.String(60), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("action_url", sa.Text(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sent_via", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("priority", sa.String(10), nullable=False, server_default="medium"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW() + INTERVAL '90 days'")),
        sa.CheckConstraint("priority IN ('low', 'medium', 'high')", name="ck_notifications_priority"),
    )
    op.create_index("idx_notifications_user_read", "notifications", ["user_id", "is_read"])
    op.create_index("idx_notifications_user_created", "notifications", ["user_id", sa.text("created_at DESC")])
    op.create_index("idx_notifications_expires", "notifications", ["expires_at"])

    # ── 6. admin_logs ─────────────────────────────────────────────────────────
    op.create_table(
        "admin_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("admin_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("admin_users.id"), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("changes", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW() + INTERVAL '30 days'")),
    )
    op.create_index("idx_admin_logs_admin_ts", "admin_logs", ["admin_id", sa.text("timestamp DESC")])
    op.create_index("idx_admin_logs_expires", "admin_logs", ["expires_at"])

    # ── 7. user_devices ───────────────────────────────────────────────────────
    op.create_table(
        "user_devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fcm_token", sa.String(500), nullable=True),
        sa.Column("device_name", sa.String(255), nullable=False, server_default="Unknown"),
        sa.Column("device_type", sa.String(20), nullable=False, server_default="web"),
        sa.Column("device_fingerprint", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_active_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("device_type IN ('web', 'pwa', 'android', 'ios')", name="ck_devices_device_type"),
    )
    op.create_index("idx_devices_user_id", "user_devices", ["user_id"])
    op.execute("CREATE UNIQUE INDEX idx_devices_fcm_token ON user_devices(fcm_token) WHERE fcm_token IS NOT NULL")
    op.create_index("idx_devices_fingerprint", "user_devices", ["user_id", "device_fingerprint"])

    # ── 8. notification_delivery_log ──────────────────────────────────────────
    op.create_table(
        "notification_delivery_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("notification_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("user_devices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("channel IN ('in_app', 'push', 'email', 'whatsapp', 'telegram')", name="ck_delivery_channel"),
        sa.CheckConstraint("status IN ('pending', 'sent', 'delivered', 'failed')", name="ck_delivery_status"),
    )
    op.create_index("idx_delivery_log_notif", "notification_delivery_log", ["notification_id"])
    op.create_index("idx_delivery_log_user", "notification_delivery_log", ["user_id", sa.text("created_at DESC")])

    # ── 9. admissions ─────────────────────────────────────────────────────────
    op.create_table(
        "admissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("slug", sa.String(500), unique=True, nullable=False),
        sa.Column("admission_name", sa.String(500), nullable=False),
        sa.Column("conducting_body", sa.String(255), nullable=False),
        sa.Column("counselling_body", sa.String(255), nullable=True),
        sa.Column("admission_type", sa.String(20), nullable=False, server_default="pg"),
        sa.Column("stream", sa.String(30), nullable=False, server_default="general"),
        sa.Column("eligibility", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("admission_details", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("selection_process", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("seats_info", postgresql.JSONB(), nullable=True),
        sa.Column("application_start", sa.Date(), nullable=True),
        sa.Column("application_end", sa.Date(), nullable=True),
        sa.Column("exam_start", sa.Date(), nullable=True),
        sa.Column("exam_end", sa.Date(), nullable=True),
        sa.Column("admission_date", sa.Date(), nullable=True),
        sa.Column("result_date", sa.Date(), nullable=True),
        sa.Column("counselling_start", sa.Date(), nullable=True),
        sa.Column("fee_general", sa.Integer(), nullable=True),
        sa.Column("fee_obc", sa.Integer(), nullable=True),
        sa.Column("fee_sc_st", sa.Integer(), nullable=True),
        sa.Column("fee_ews", sa.Integer(), nullable=True),
        sa.Column("fee_female", sa.Integer(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("short_description", sa.Text(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("admission_type IN ('ug', 'pg', 'doctoral', 'lateral')", name="ck_admission_type"),
        sa.CheckConstraint("stream IN ('medical', 'engineering', 'law', 'management', 'arts_science', 'general')", name="ck_admission_stream"),
        sa.CheckConstraint("status IN ('upcoming', 'active', 'inactive', 'closed')", name="ck_admission_status"),
    )
    op.create_index("idx_admissions_slug", "admissions", ["slug"], unique=True)
    op.create_index("idx_admissions_stream_status", "admissions", ["stream", "status", "created_at"])
    op.execute("""
        ALTER TABLE admissions ADD COLUMN search_vector tsvector
            GENERATED ALWAYS AS (
                setweight(to_tsvector('english', coalesce(admission_name, '')), 'A') ||
                setweight(to_tsvector('english', coalesce(conducting_body, '')), 'B') ||
                setweight(to_tsvector('english', coalesce(description, '')), 'C')
            ) STORED
    """)
    op.execute("CREATE INDEX idx_admissions_search ON admissions USING GIN(search_vector)")

    # ── 10. admit_cards ───────────────────────────────────────────────────────
    op.create_table(
        "admit_cards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True),
        sa.Column("admission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("admissions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(500), nullable=False, unique=True),
        sa.Column("links", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("exam_start", sa.Date(), nullable=True),
        sa.Column("exam_end", sa.Date(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "(job_id IS NOT NULL AND admission_id IS NULL) OR (job_id IS NULL AND admission_id IS NOT NULL)",
            name="ck_admit_cards_source",
        ),
    )
    op.create_index("idx_admit_cards_job", "admit_cards", ["job_id"])
    op.create_index("idx_admit_cards_admission", "admit_cards", ["admission_id"])
    op.create_index("idx_admit_cards_pub", "admit_cards", ["published_at"])
    op.create_index("ix_admit_cards_slug", "admit_cards", ["slug"], unique=True)

    # ── 11. answer_keys ───────────────────────────────────────────────────────
    op.create_table(
        "answer_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True),
        sa.Column("admission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("admissions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(500), nullable=False, unique=True),
        sa.Column("links", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "(job_id IS NOT NULL AND admission_id IS NULL) OR (job_id IS NULL AND admission_id IS NOT NULL)",
            name="ck_answer_keys_source",
        ),
    )
    op.create_index("idx_answer_keys_job", "answer_keys", ["job_id"])
    op.create_index("idx_answer_keys_admission", "answer_keys", ["admission_id"])
    op.create_index("ix_answer_keys_slug", "answer_keys", ["slug"], unique=True)

    # ── 12. results ───────────────────────────────────────────────────────────
    op.create_table(
        "results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True),
        sa.Column("admission_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("admissions.id", ondelete="CASCADE"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(500), nullable=False, unique=True),
        sa.Column("links", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "(job_id IS NOT NULL AND admission_id IS NULL) OR (job_id IS NULL AND admission_id IS NOT NULL)",
            name="ck_results_source",
        ),
    )
    op.create_index("idx_results_job", "results", ["job_id"])
    op.create_index("idx_results_admission", "results", ["admission_id"])
    op.create_index("idx_results_pub", "results", ["published_at"])
    op.create_index("ix_results_slug", "results", ["slug"], unique=True)

    # ── 13. user_tracks ───────────────────────────────────────────────────────
    op.create_table(
        "user_tracks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_type", sa.String(10), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("user_id", "entity_type", "entity_id", name="uq_user_track"),
        sa.CheckConstraint("entity_type IN ('job', 'admission')", name="ck_user_tracks_entity_type"),
    )
    op.create_index("ix_user_tracks_user_id", "user_tracks", ["user_id"])
    op.create_index("ix_user_tracks_entity", "user_tracks", ["entity_type", "entity_id"])


def downgrade() -> None:
    op.drop_table("user_tracks")
    op.drop_table("results")
    op.drop_table("answer_keys")
    op.drop_table("admit_cards")
    op.drop_table("admissions")
    op.drop_table("notification_delivery_log")
    op.drop_table("user_devices")
    op.drop_table("admin_logs")
    op.drop_table("notifications")
    op.drop_table("jobs")
    op.drop_table("user_profiles")
    op.drop_table("admin_users")
    op.drop_table("users")
