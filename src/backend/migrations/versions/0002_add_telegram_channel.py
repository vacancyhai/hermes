"""Add telegram to ck_delivery_channel constraint.

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-24

Adds 'telegram' as a valid delivery channel in notification_delivery_log.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("ck_delivery_channel", "notification_delivery_log", type_="check")
    op.create_check_constraint(
        "ck_delivery_channel",
        "notification_delivery_log",
        "channel IN ('in_app','push','email','whatsapp','telegram')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_delivery_channel", "notification_delivery_log", type_="check")
    op.create_check_constraint(
        "ck_delivery_channel",
        "notification_delivery_log",
        "channel IN ('in_app','push','email','whatsapp')",
    )
