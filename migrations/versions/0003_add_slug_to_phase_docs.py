"""Add slug field to admit_cards, answer_keys, and results tables.

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add slug column to admit_cards (nullable first)
    op.add_column(
        "admit_cards",
        sa.Column("slug", sa.String(length=500), nullable=True),
    )
    # Generate unique slugs for existing rows
    op.execute("""
        UPDATE admit_cards
        SET slug = 'admit-card-' || id::text
        WHERE slug IS NULL
    """)
    op.alter_column("admit_cards", "slug", nullable=False)
    op.create_index("ix_admit_cards_slug", "admit_cards", ["slug"], unique=True)

    # Add slug column to answer_keys (nullable first)
    op.add_column(
        "answer_keys",
        sa.Column("slug", sa.String(length=500), nullable=True),
    )
    # Generate unique slugs for existing rows
    op.execute("""
        UPDATE answer_keys
        SET slug = 'answer-key-' || id::text
        WHERE slug IS NULL
    """)
    op.alter_column("answer_keys", "slug", nullable=False)
    op.create_index("ix_answer_keys_slug", "answer_keys", ["slug"], unique=True)

    # Add slug column to results (nullable first)
    op.add_column(
        "results",
        sa.Column("slug", sa.String(length=500), nullable=True),
    )
    # Generate unique slugs for existing rows
    op.execute("""
        UPDATE results
        SET slug = 'result-' || id::text
        WHERE slug IS NULL
    """)
    op.alter_column("results", "slug", nullable=False)
    op.create_index("ix_results_slug", "results", ["slug"], unique=True)


def downgrade() -> None:
    # Remove slug column from results
    op.drop_index("ix_results_slug", table_name="results")
    op.drop_column("results", "slug")

    # Remove slug column from answer_keys
    op.drop_index("ix_answer_keys_slug", table_name="answer_keys")
    op.drop_column("answer_keys", "slug")

    # Remove slug column from admit_cards
    op.drop_index("ix_admit_cards_slug", table_name="admit_cards")
    op.drop_column("admit_cards", "slug")
