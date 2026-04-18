"""Remove files column from answer_keys table.

Revision ID: 0004_remove_files_from_answer_keys
Revises: 0003_answer_key_result_dates
Create Date: 2026-04-18
"""

from alembic import op

revision = "0004_rm_files_answer_keys"
down_revision = "0003_answer_key_result_dates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("answer_keys", "files")


def downgrade() -> None:
    import sqlalchemy as sa
    from sqlalchemy.dialects import postgresql

    op.add_column(
        "answer_keys",
        sa.Column(
            "files",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
    )
