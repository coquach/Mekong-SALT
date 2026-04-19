"""remove auth

Revision ID: 0004_remove_auth
Revises: 0003_mvp_operational_workflow
Create Date: 2026-04-14 23:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0004_remove_auth"
down_revision: str | None = "0003_mvp_operational_workflow"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Drop user table and auth-linked approval fields."""
    op.drop_index(op.f("ix_approvals_decided_by_user_id"), table_name="approvals")
    op.drop_constraint(op.f("fk_approvals_decided_by_user_id_users"), "approvals", type_="foreignkey")
    op.drop_column("approvals", "decided_by_user_id")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_role"), table_name="users")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS user_role")


def downgrade() -> None:
    """Recreate user table and auth-linked approval fields."""
    op.execute(
        "CREATE TYPE user_role AS ENUM ('admin', 'supervisor', 'operator', 'viewer')"
    )
    op.create_table(
        "users",
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("role", sa.Enum("admin", "supervisor", "operator", "viewer", name="user_role"), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        op.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        op.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)
    op.add_column("approvals", sa.Column("decided_by_user_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        op.f("fk_approvals_decided_by_user_id_users"),
        "approvals",
        "users",
        ["decided_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_approvals_decided_by_user_id"), "approvals", ["decided_by_user_id"], unique=False)
