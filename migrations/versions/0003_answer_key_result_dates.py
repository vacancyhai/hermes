"""Replace objection_deadline/result_type with start_date/end_date on answer_keys and results.

Revision ID: 0003_answer_key_result_dates
Revises: 0002_add_links_to_docs
Create Date: 2026-04-18
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_answer_key_result_dates"
down_revision = "0002_add_links_to_docs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("answer_keys", "objection_deadline")
    op.add_column("answer_keys", sa.Column("start_date", sa.Date(), nullable=True))
    op.add_column("answer_keys", sa.Column("end_date", sa.Date(), nullable=True))

    op.drop_constraint("ck_result_type", "results", type_="check")
    op.drop_column("results", "result_type")
    op.add_column("results", sa.Column("start_date", sa.Date(), nullable=True))
    op.add_column("results", sa.Column("end_date", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("results", "end_date")
    op.drop_column("results", "start_date")
    op.add_column("results", sa.Column("result_type", sa.String(20), nullable=False, server_default="merit_list"))
    op.create_check_constraint("ck_result_type", "results", "result_type IN ('shortlist', 'cutoff', 'merit_list', 'final')")

    op.drop_column("answer_keys", "end_date")
    op.drop_column("answer_keys", "start_date")
    op.add_column("answer_keys", sa.Column("objection_deadline", sa.Date(), nullable=True))
