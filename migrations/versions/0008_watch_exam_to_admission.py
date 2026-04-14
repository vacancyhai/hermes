"""Rename entity_type value 'exam' → 'admission' in user_watches; update CHECK constraint.

Revision ID: 0008_watch_exam_to_admission
Revises: 0007_rename_admission_columns
Create Date: 2026-04-11
"""

from alembic import op

revision = "0008_watch_exam_to_admission"
down_revision = "0007_rename_admission_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_user_watches_entity_type", "user_watches", type_="check")
    op.execute("UPDATE user_watches SET entity_type = 'admission' WHERE entity_type = 'exam'")
    op.create_check_constraint(
        "ck_user_watches_entity_type",
        "user_watches",
        "entity_type IN ('job', 'admission')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_user_watches_entity_type", "user_watches", type_="check")
    op.execute("UPDATE user_watches SET entity_type = 'exam' WHERE entity_type = 'admission'")
    op.create_check_constraint(
        "ck_user_watches_entity_type",
        "user_watches",
        "entity_type IN ('job', 'exam')",
    )
