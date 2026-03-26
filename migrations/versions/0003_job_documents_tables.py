"""Add job_admit_cards, job_answer_keys, job_results tables; remove admission/yojana from job_type.

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-24
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Update ck_jobs_job_type: remove 'admission' and 'yojana' ──────────
    op.drop_constraint("ck_jobs_job_type", "job_vacancies", type_="check")
    op.create_check_constraint(
        "ck_jobs_job_type",
        "job_vacancies",
        "job_type IN ('latest_job','result','admit_card','answer_key')",
    )

    # ── 2. job_admit_cards ────────────────────────────────────────────────────
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

    # ── 3. job_answer_keys ────────────────────────────────────────────────────
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

    # ── 4. job_results ────────────────────────────────────────────────────────
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

    op.drop_constraint("ck_jobs_job_type", "job_vacancies", type_="check")
    op.create_check_constraint(
        "ck_jobs_job_type",
        "job_vacancies",
        "job_type IN ('latest_job','result','admit_card','answer_key','admission','yojana')",
    )
