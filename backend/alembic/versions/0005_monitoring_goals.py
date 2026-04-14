"""monitoring goals

Revision ID: 0005_monitoring_goals
Revises: 0004_remove_auth
Create Date: 2026-04-15 09:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0005_monitoring_goals"
down_revision: str | None = "0004_remove_auth"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Create monitoring goals table for Phase 2 scheduling domain."""
    op.create_table(
        "monitoring_goals",
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("region_id", sa.UUID(), nullable=False),
        sa.Column("station_id", sa.UUID(), nullable=True),
        sa.Column("objective", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=30), nullable=True),
        sa.Column("warning_threshold_dsm", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("critical_threshold_dsm", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("evaluation_interval_minutes", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_run_status", sa.String(length=30), nullable=True),
        sa.Column("last_run_plan_id", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "warning_threshold_dsm > 0",
            name=op.f("ck_monitoring_goals_monitoring_goal_warning_threshold_positive"),
        ),
        sa.CheckConstraint(
            "critical_threshold_dsm > warning_threshold_dsm",
            name=op.f("ck_monitoring_goals_monitoring_goal_critical_gt_warning"),
        ),
        sa.CheckConstraint(
            "evaluation_interval_minutes >= 1",
            name=op.f("ck_monitoring_goals_monitoring_goal_interval_positive"),
        ),
        sa.ForeignKeyConstraint(
            ["last_run_plan_id"],
            ["action_plans.id"],
            name=op.f("fk_monitoring_goals_last_run_plan_id_action_plans"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["region_id"],
            ["regions.id"],
            name=op.f("fk_monitoring_goals_region_id_regions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["station_id"],
            ["sensor_stations.id"],
            name=op.f("fk_monitoring_goals_station_id_sensor_stations"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_monitoring_goals")),
    )
    op.create_index(op.f("ix_monitoring_goals_name"), "monitoring_goals", ["name"], unique=True)
    op.create_index(op.f("ix_monitoring_goals_region_id"), "monitoring_goals", ["region_id"], unique=False)
    op.create_index(op.f("ix_monitoring_goals_station_id"), "monitoring_goals", ["station_id"], unique=False)
    op.create_index(op.f("ix_monitoring_goals_is_active"), "monitoring_goals", ["is_active"], unique=False)


def downgrade() -> None:
    """Drop monitoring goals table."""
    op.drop_index(op.f("ix_monitoring_goals_is_active"), table_name="monitoring_goals")
    op.drop_index(op.f("ix_monitoring_goals_station_id"), table_name="monitoring_goals")
    op.drop_index(op.f("ix_monitoring_goals_region_id"), table_name="monitoring_goals")
    op.drop_index(op.f("ix_monitoring_goals_name"), table_name="monitoring_goals")
    op.drop_table("monitoring_goals")
