"""Separate admin_users from users table.

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-22

- Create admin_users table for admin/operator accounts
- Migrate existing admin/operator rows from users → admin_users
- Update admin_logs.admin_id FK to reference admin_users
- Update job_vacancies.created_by FK to reference admin_users
- Drop role column from users table (all remaining are regular users)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create admin_users table
    op.create_table(
        "admin_users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20)),
        sa.Column("role", sa.String(20), nullable=False, server_default="operator"),
        sa.Column("department", sa.String(255)),
        sa.Column("permissions", JSONB, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("is_email_verified", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("last_login", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("role IN ('admin','operator')", name="ck_admin_users_role"),
        sa.CheckConstraint("status IN ('active','suspended','deleted')", name="ck_admin_users_status"),
    )
    op.create_index("idx_admin_users_email", "admin_users", ["email"])
    op.create_index("idx_admin_users_status", "admin_users", ["status"])

    # 2. Migrate existing admin/operator rows from users → admin_users
    op.execute("""
        INSERT INTO admin_users (id, email, password_hash, full_name, phone, role, status, is_email_verified, last_login, created_at, updated_at)
        SELECT id, email, password_hash, full_name, phone, role, status, is_email_verified, last_login, created_at, updated_at
        FROM users
        WHERE role IN ('admin', 'operator')
    """)

    # 3. Update admin_logs FK: drop old FK, add new one pointing to admin_users
    op.drop_constraint("admin_logs_admin_id_fkey", "admin_logs", type_="foreignkey")
    op.create_foreign_key("admin_logs_admin_id_fkey", "admin_logs", "admin_users", ["admin_id"], ["id"])

    # 4. Update job_vacancies.created_by FK: drop old, add new
    op.drop_constraint("job_vacancies_created_by_fkey", "job_vacancies", type_="foreignkey")
    op.create_foreign_key("job_vacancies_created_by_fkey", "job_vacancies", "admin_users", ["created_by"], ["id"])

    # 5. Delete migrated admin/operator rows from users
    op.execute("DELETE FROM users WHERE role IN ('admin', 'operator')")

    # 6. Drop role-related check constraint and column from users
    op.drop_constraint("ck_users_role", "users", type_="check")
    op.drop_column("users", "role")


def downgrade() -> None:
    # 1. Re-add role column to users
    op.add_column("users", sa.Column("role", sa.String(20), nullable=False, server_default="user"))
    op.create_check_constraint("ck_users_role", "users", "role IN ('user','admin','operator')")

    # 2. Migrate admin rows back to users
    op.execute("""
        INSERT INTO users (id, email, password_hash, full_name, phone, role, status, is_email_verified, last_login, created_at, updated_at)
        SELECT id, email, password_hash, full_name, phone, role, status, is_email_verified, last_login, created_at, updated_at
        FROM admin_users
    """)

    # 3. Restore FK on admin_logs
    op.drop_constraint("admin_logs_admin_id_fkey", "admin_logs", type_="foreignkey")
    op.create_foreign_key("admin_logs_admin_id_fkey", "admin_logs", "users", ["admin_id"], ["id"])

    # 4. Restore FK on job_vacancies
    op.drop_constraint("job_vacancies_created_by_fkey", "job_vacancies", type_="foreignkey")
    op.create_foreign_key("job_vacancies_created_by_fkey", "job_vacancies", "users", ["created_by"], ["id"])

    # 5. Drop admin_users table
    op.drop_table("admin_users")
