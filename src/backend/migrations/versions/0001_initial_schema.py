"""Initial schema — 6 core tables.

Revision ID: 0001
Revises: None
Create Date: 2026-03-21

Tables: users, user_profiles, job_vacancies, user_job_applications,
        notifications, admin_logs
Matches: DESIGN.md Database Schema section exactly.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID, ARRAY, INET

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20)),
        sa.Column("role", sa.String(20), nullable=False, server_default="user"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("is_email_verified", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("last_login", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('user','admin','operator')", name="ck_users_role"),
        sa.CheckConstraint("status IN ('active','suspended','deleted')", name="ck_users_status"),
    )
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_status", "users", ["status"])

    # 2. user_profiles
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
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("gender IN ('Male','Female','Other')", name="ck_profiles_gender"),
        sa.CheckConstraint("category IN ('General','OBC','SC','ST','EWS','EBC')", name="ck_profiles_category"),
    )
    op.create_index("idx_user_profiles_user_id", "user_profiles", ["user_id"], unique=True)
    op.create_index("idx_user_profiles_education", "user_profiles", ["education"], postgresql_using="gin")
    op.create_index("idx_user_profiles_notif_prefs", "user_profiles", ["notification_preferences"], postgresql_using="gin")

    # 3. job_vacancies
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
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("is_featured", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("is_urgent", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("views", sa.Integer, nullable=False, server_default="0"),
        sa.Column("applications_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("source", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("job_type IN ('latest_job','result','admit_card','answer_key','admission','yojana')", name="ck_jobs_job_type"),
        sa.CheckConstraint("employment_type IN ('permanent','temporary','contract','apprentice')", name="ck_jobs_employment_type"),
        sa.CheckConstraint("status IN ('draft','active','expired','cancelled','upcoming')", name="ck_jobs_status"),
        sa.CheckConstraint("source IN ('manual','pdf_upload')", name="ck_jobs_source"),
    )
    op.create_index("idx_jobs_organization", "job_vacancies", ["organization"])
    op.create_index("idx_jobs_status_created", "job_vacancies", ["status", sa.text("created_at DESC")])
    op.create_index("idx_jobs_qual_level", "job_vacancies", ["qualification_level"])
    op.create_index("idx_jobs_application_end", "job_vacancies", ["application_end"])
    op.create_index("idx_jobs_org_status", "job_vacancies", ["organization", "status", sa.text("created_at DESC")])
    op.create_index("idx_jobs_eligibility_gin", "job_vacancies", ["eligibility"], postgresql_using="gin")

    # Full-text search vector (generated column)
    op.execute("""
        ALTER TABLE job_vacancies ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('english', coalesce(job_title, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(organization, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(description, '')), 'C')
        ) STORED
    """)
    op.execute("CREATE INDEX idx_jobs_search ON job_vacancies USING GIN (search_vector)")

    # 4. user_job_applications
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
            "status IN ('applied','admit_card_released','exam_completed','result_pending','selected','rejected','waiting_list')",
            name="ck_applications_status",
        ),
    )
    op.create_index("idx_applications_user_job", "user_job_applications", ["user_id", "job_id"])
    op.create_index("idx_applications_user_applied", "user_job_applications", ["user_id", sa.text("applied_on DESC")])

    # 5. notifications
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
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW() + INTERVAL '90 days'")),
        sa.CheckConstraint(
            "entity_type IN ('job','result','admit_card','answer_key','admission','yojana')",
            name="ck_notifications_entity_type",
        ),
        sa.CheckConstraint("priority IN ('low','medium','high')", name="ck_notifications_priority"),
    )
    op.create_index("idx_notifications_user_read", "notifications", ["user_id", "is_read"])
    op.create_index("idx_notifications_user_created", "notifications", ["user_id", sa.text("created_at DESC")])
    op.create_index("idx_notifications_expires", "notifications", ["expires_at"])

    # 6. admin_logs
    op.create_table(
        "admin_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("admin_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100)),
        sa.Column("resource_id", UUID(as_uuid=True)),
        sa.Column("details", sa.Text),
        sa.Column("changes", JSONB, nullable=False, server_default="{}"),
        sa.Column("ip_address", INET),
        sa.Column("user_agent", sa.Text),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW() + INTERVAL '30 days'")),
    )
    op.create_index("idx_admin_logs_admin_ts", "admin_logs", ["admin_id", sa.text("timestamp DESC")])
    op.create_index("idx_admin_logs_expires", "admin_logs", ["expires_at"])


def downgrade() -> None:
    op.drop_table("admin_logs")
    op.drop_table("notifications")
    op.drop_table("user_job_applications")
    op.drop_table("job_vacancies")
    op.drop_table("user_profiles")
    op.drop_table("users")
