"""Add links JSONB column to admit_cards, answer_keys, results.

Revision ID: 0002_add_links_to_docs
Revises: 0001_initial
Create Date: 2026-04-18
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_add_links_to_docs"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "admit_cards",
        sa.Column(
            "links",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
    )
    op.add_column(
        "answer_keys",
        sa.Column(
            "links",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
    )
    op.add_column(
        "results",
        sa.Column(
            "links",
            postgresql.JSONB(),
            nullable=False,
            server_default="[]",
        ),
    )


def downgrade() -> None:
    op.drop_column("results", "links")
    op.drop_column("answer_keys", "links")
    op.drop_column("admit_cards", "links")
