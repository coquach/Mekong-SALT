"""execution batches

Revision ID: 0008_execution_batches
Revises: 0007_active_monitoring_worker
Create Date: 2026-04-15 16:45:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0008_execution_batches"
down_revision: str | None = "0007_active_monitoring_worker"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Create persistent execution batches and link action executions to batch_id."""
    execution_status = postgresql.ENUM(
        "pending",
        "running",
        "succeeded",
        "failed",
        "cancelled",
        name="execution_status",
        create_type=False,
    )

    op.create_table(
        "execution_batches",
        sa.Column("plan_id", sa.UUID(), nullable=False),
        sa.Column("region_id", sa.UUID(), nullable=False),
        sa.Column("status", execution_status, nullable=False),
        sa.Column("simulated", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("idempotency_key", sa.String(length=120), nullable=True),
        sa.Column("requested_by", sa.String(length=255), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["plan_id"], ["action_plans.id"], name=op.f("fk_execution_batches_plan_id_action_plans"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"], name=op.f("fk_execution_batches_region_id_regions"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_execution_batches")),
        sa.UniqueConstraint("idempotency_key", name=op.f("uq_execution_batches_idempotency_key")),
    )
    op.create_index(op.f("ix_execution_batches_plan_id"), "execution_batches", ["plan_id"], unique=False)
    op.create_index(op.f("ix_execution_batches_region_id"), "execution_batches", ["region_id"], unique=False)
    op.create_index(op.f("ix_execution_batches_status"), "execution_batches", ["status"], unique=False)
    op.create_index(op.f("ix_execution_batches_started_at"), "execution_batches", ["started_at"], unique=False)

    op.add_column("action_executions", sa.Column("batch_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        op.f("fk_action_executions_batch_id_execution_batches"),
        "action_executions",
        "execution_batches",
        ["batch_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_action_executions_batch_id"), "action_executions", ["batch_id"], unique=False)

    op.alter_column("execution_batches", "simulated", server_default=None)


def downgrade() -> None:
    """Drop execution batch schema changes."""
    op.drop_index(op.f("ix_action_executions_batch_id"), table_name="action_executions")
    op.drop_constraint(op.f("fk_action_executions_batch_id_execution_batches"), "action_executions", type_="foreignkey")
    op.drop_column("action_executions", "batch_id")

    op.drop_index(op.f("ix_execution_batches_started_at"), table_name="execution_batches")
    op.drop_index(op.f("ix_execution_batches_status"), table_name="execution_batches")
    op.drop_index(op.f("ix_execution_batches_region_id"), table_name="execution_batches")
    op.drop_index(op.f("ix_execution_batches_plan_id"), table_name="execution_batches")
    op.drop_table("execution_batches")
