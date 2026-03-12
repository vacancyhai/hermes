"""Create admin_users table

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0002'
down_revision: Union[str, None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # ADMIN USERS TABLE
    # ------------------------------------------------------------------
    op.create_table(
        'admin_users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('username', sa.String(100), unique=True, nullable=False),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='operator'),
        sa.Column('permissions', postgresql.JSONB, nullable=False, server_default='{}'),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('is_verified', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('is_2fa_enabled', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('failed_login_attempts', sa.Integer, nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(timezone=True)),
        sa.Column('last_login', sa.DateTime(timezone=True)),
        sa.Column('last_login_ip', postgresql.INET),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('admin_users.id', ondelete='SET NULL')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('admin_users.id', ondelete='SET NULL')),
        sa.CheckConstraint("role IN ('admin', 'operator')", name='ck_admin_users_role'),
        sa.CheckConstraint("status IN ('active', 'suspended', 'inactive')", name='ck_admin_users_status'),
    )
    
    # Indexes
    op.create_index('idx_admin_users_username', 'admin_users', ['username'], unique=True)
    op.create_index('idx_admin_users_email', 'admin_users', ['email'], unique=True)
    op.create_index('idx_admin_users_role', 'admin_users', ['role'])
    op.create_index('idx_admin_users_status', 'admin_users', ['status'])
    op.create_index('idx_admin_users_permissions', 'admin_users', ['permissions'], postgresql_using='gin')
    
    # ------------------------------------------------------------------
    # UPDATE ADMIN_LOGS TO REFERENCE ADMIN_USERS
    # ------------------------------------------------------------------
    # Drop existing foreign key constraint (if any)
    op.drop_constraint('admin_logs_admin_id_fkey', 'admin_logs', type_='foreignkey')
    
    # Add new foreign key to admin_users
    op.create_foreign_key(
        'admin_logs_admin_id_fkey',
        'admin_logs',
        'admin_users',
        ['admin_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # ------------------------------------------------------------------
    # UPDATE ACCESS_AUDIT_LOGS TO REFERENCE ADMIN_USERS
    # ------------------------------------------------------------------
    # Drop existing foreign key constraint (if any)
    op.drop_constraint('access_audit_logs_admin_id_fkey', 'access_audit_logs', type_='foreignkey')
    
    # Add new foreign key to admin_users
    op.create_foreign_key(
        'access_audit_logs_admin_id_fkey',
        'access_audit_logs',
        'admin_users',
        ['admin_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Restore foreign keys to users table
    op.drop_constraint('access_audit_logs_admin_id_fkey', 'access_audit_logs', type_='foreignkey')
    op.create_foreign_key(
        'access_audit_logs_admin_id_fkey',
        'access_audit_logs',
        'users',
        ['admin_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    op.drop_constraint('admin_logs_admin_id_fkey', 'admin_logs', type_='foreignkey')
    op.create_foreign_key(
        'admin_logs_admin_id_fkey',
        'admin_logs',
        'users',
        ['admin_id'],
        ['id'],
        ondelete='CASCADE'
    )
    
    # Drop admin_users table
    op.drop_index('idx_admin_users_permissions', 'admin_users')
    op.drop_index('idx_admin_users_status', 'admin_users')
    op.drop_index('idx_admin_users_role', 'admin_users')
    op.drop_index('idx_admin_users_email', 'admin_users')
    op.drop_index('idx_admin_users_username', 'admin_users')
    op.drop_table('admin_users')
