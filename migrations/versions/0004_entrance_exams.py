"""Add entrance_exams table and exam_id FK to document tables.

Revision ID: 0004
Revises: 0003
Create Date: 2026-03-24

Creates a separate entrance_exams table for admission/entrance exams (NEET,
JEE, CLAT, CAT etc.) distinct from government job vacancies. Extends the 3
existing document tables with an exam_id FK so admit cards, answer keys, and
results can be linked to either a job or an entrance exam.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. entrance_exams ────────────────────────────────────────────────────
    op.create_table(
        "entrance_exams",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("slug", sa.String(500), unique=True, nullable=False),
        sa.Column("exam_name", sa.String(500), nullable=False),
        sa.Column("conducting_body", sa.String(255), nullable=False),
        sa.Column("counselling_body", sa.String(255), nullable=True),
        sa.Column("exam_type", sa.String(20), nullable=False, server_default="pg"),
        sa.Column("stream", sa.String(30), nullable=False, server_default="general"),
        sa.Column("eligibility", JSONB, nullable=False, server_default="{}"),
        sa.Column("exam_details", JSONB, nullable=False, server_default="{}"),
        sa.Column("selection_process", JSONB, nullable=False, server_default="[]"),
        sa.Column("seats_info", JSONB, nullable=True),
        sa.Column("application_start", sa.Date, nullable=True),
        sa.Column("application_end", sa.Date, nullable=True),
        sa.Column("exam_date", sa.Date, nullable=True),
        sa.Column("result_date", sa.Date, nullable=True),
        sa.Column("counselling_start", sa.Date, nullable=True),
        sa.Column("fee_general", sa.Integer, nullable=True),
        sa.Column("fee_obc", sa.Integer, nullable=True),
        sa.Column("fee_sc_st", sa.Integer, nullable=True),
        sa.Column("fee_ews", sa.Integer, nullable=True),
        sa.Column("fee_female", sa.Integer, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("short_description", sa.Text, nullable=True),
        sa.Column("source_url", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("is_featured", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("views", sa.Integer, nullable=False, server_default="0"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "exam_type IN ('ug','pg','doctoral','lateral')",
            name="ck_exam_type",
        ),
        sa.CheckConstraint(
            "stream IN ('medical','engineering','law','management','arts_science','general')",
            name="ck_exam_stream",
        ),
        sa.CheckConstraint(
            "status IN ('upcoming','active','completed','cancelled')",
            name="ck_exam_status",
        ),
    )
    op.create_index("idx_exams_slug", "entrance_exams", ["slug"], unique=True)
    op.create_index("idx_exams_stream_status", "entrance_exams", ["stream", "status", "created_at"])

    # Add full-text search vector column
    op.execute("""
        ALTER TABLE entrance_exams
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('english', coalesce(exam_name, '')), 'A') ||
            setweight(to_tsvector('english', coalesce(conducting_body, '')), 'B') ||
            setweight(to_tsvector('english', coalesce(description, '')), 'C')
        ) STORED
    """)
    op.create_index("idx_exams_search", "entrance_exams", ["search_vector"],
                    postgresql_using="gin")

    # ── 2. Add exam_id FK to the 3 document tables ────────────────────────────
    for table in ("job_admit_cards", "job_answer_keys", "job_results"):
        op.add_column(table, sa.Column("exam_id", UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(
            f"fk_{table}_exam_id",
            table, "entrance_exams",
            ["exam_id"], ["id"],
            ondelete="CASCADE",
        )
        # Make job_id nullable so exam-linked docs don't require a job
        op.alter_column(table, "job_id", nullable=True)
        op.create_check_constraint(
            f"ck_{table}_source",
            table,
            "(job_id IS NOT NULL AND exam_id IS NULL) OR (job_id IS NULL AND exam_id IS NOT NULL)",
        )
        op.create_index(f"idx_{table}_exam", table, ["exam_id", "phase_number"])


def downgrade() -> None:
    for table in ("job_admit_cards", "job_answer_keys", "job_results"):
        op.drop_constraint(f"ck_{table}_source", table, type_="check")
        op.drop_constraint(f"fk_{table}_exam_id", table, type_="foreignkey")
        op.drop_index(f"idx_{table}_exam", table_name=table)
        op.drop_column(table, "exam_id")
        op.alter_column(table, "job_id", nullable=False)

    op.drop_table("entrance_exams")
