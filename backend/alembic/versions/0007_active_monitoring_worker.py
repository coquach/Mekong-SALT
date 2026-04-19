"""active monitoring worker fields

Revision ID: 0007_active_monitoring_worker
Revises: 0006_agent_runs_obs
Create Date: 2026-04-15 11:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0007_active_monitoring_worker"
down_revision: str | None = "0006_agent_runs_obs"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Add goal-level auto-plan control for Phase 4 worker runs."""
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


def downgrade() -> None:
    """Remove Phase 4 auto-plan control."""
    op.drop_column("monitoring_goals", "auto_plan_enabled")
