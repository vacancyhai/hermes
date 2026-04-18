"""Remove total_qualified and cutoff_marks from results table.

Revision ID: 0005_rm_total_qual_cutoff
Revises: 0004_rm_files_answer_keys
Create Date: 2026-04-18
"""

from alembic import op

revision = "0005_rm_total_qual_cutoff"
down_revision = "0004_rm_files_answer_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("results", "total_qualified")
    op.drop_column("results", "cutoff_marks")


def downgrade() -> None:
    import sqlalchemy as sa
    from sqlalchemy.dialects import postgresql

    op.add_column("results", sa.Column("cutoff_marks", postgresql.JSONB(), nullable=True))
    op.add_column("results", sa.Column("total_qualified", sa.Integer(), nullable=True))
