"""monitoring goal last processed reading

Revision ID: 0015_goal_last_processed_reading
Revises: 0014_registry_retry_meta
Create Date: 2026-04-17 17:10:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0015_goal_last_processed_reading"
down_revision: str | None = "0014_registry_retry_meta"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Persist latest processed reading to deduplicate monitoring cycles."""
    op.add_column(
        "monitoring_goals",
        sa.Column("last_processed_reading_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        op.f("fk_monitoring_goals_last_processed_reading_id_sensor_readings"),
        "monitoring_goals",
        "sensor_readings",
        ["last_processed_reading_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_monitoring_goals_last_processed_reading_id"),
        "monitoring_goals",
        ["last_processed_reading_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove processed-reading deduplication state from goals."""
    op.drop_index(op.f("ix_monitoring_goals_last_processed_reading_id"), table_name="monitoring_goals")
    op.drop_constraint(
        op.f("fk_monitoring_goals_last_processed_reading_id_sensor_readings"),
        "monitoring_goals",
        type_="foreignkey",
    )
    op.drop_column("monitoring_goals", "last_processed_reading_id")
