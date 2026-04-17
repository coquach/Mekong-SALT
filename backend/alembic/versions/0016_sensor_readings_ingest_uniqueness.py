"""sensor readings ingest uniqueness

Revision ID: 0016_ingest_uniqueness
Revises: 0015_goal_last_processed_reading
Create Date: 2026-04-17 20:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0016_ingest_uniqueness"
down_revision: str | None = "0015_goal_last_processed_reading"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Enforce hard idempotency for ingest writes."""
    op.execute(
        """
        WITH ranked AS (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY station_id, recorded_at, source
                    ORDER BY created_at ASC, id ASC
                ) AS row_num
            FROM sensor_readings
        )
        DELETE FROM sensor_readings AS duplicate
        USING ranked
        WHERE duplicate.id = ranked.id
          AND ranked.row_num > 1
        """
    )
    op.create_unique_constraint(
        "uq_sensor_readings_station_recorded_source",
        "sensor_readings",
        ["station_id", "recorded_at", "source"],
    )


def downgrade() -> None:
    """Remove ingest uniqueness guard."""
    op.drop_constraint(
        "uq_sensor_readings_station_recorded_source",
        "sensor_readings",
        type_="unique",
    )
