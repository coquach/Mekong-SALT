"""remove monitoring goal auto plan enabled

Revision ID: 0018_remove_monitoring_goal_auto_plan_enabled
Revises: 0017_gate_management
Create Date: 2026-04-18 00:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0018_remove_monitoring_goal_auto_plan_enabled"
down_revision: str | None = "0017_gate_management"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Drop goal-level auto-plan control in favor of risk-based gating."""
    op.drop_column("monitoring_goals", "auto_plan_enabled")


def downgrade() -> None:
    """Restore goal-level auto-plan control for backward compatibility."""
    op.add_column(
        "monitoring_goals",
        sa.Column(
            "auto_plan_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.alter_column("monitoring_goals", "auto_plan_enabled", server_default=None)
