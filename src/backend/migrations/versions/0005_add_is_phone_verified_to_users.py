"""add_is_phone_verified_to_users

Revision ID: 0005
Revises: 0004
Create Date: 2026-03-25 21:51:08.091691
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0005'
down_revision: Union[str, None] = '0004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add is_phone_verified column to users table
    op.add_column('users', sa.Column('is_phone_verified', sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    # Remove is_phone_verified column from users table
    op.drop_column('users', 'is_phone_verified')
