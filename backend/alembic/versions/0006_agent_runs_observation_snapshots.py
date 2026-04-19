"""agent runs and observation snapshots

Revision ID: 0006_agent_runs_obs
Revises: 0005_monitoring_goals
Create Date: 2026-04-15 10:45:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0006_agent_runs_obs"
down_revision: str | None = "0005_monitoring_goals"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Create run trace and pre-decision observation snapshot tables."""
    op.create_table(
        "agent_runs",
        sa.Column("run_type", sa.String(length=50), nullable=False),
        sa.Column("trigger_source", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("trace", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("region_id", sa.UUID(), nullable=True),
        sa.Column("station_id", sa.UUID(), nullable=True),
        sa.Column("risk_assessment_id", sa.UUID(), nullable=True),
        sa.Column("incident_id", sa.UUID(), nullable=True),
        sa.Column("action_plan_id", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint(
            "status IN ('started', 'succeeded', 'failed', 'skipped')",
            name=op.f("ck_agent_runs_agent_run_status_valid"),
        ),
        sa.ForeignKeyConstraint(["action_plan_id"], ["action_plans.id"], name=op.f("fk_agent_runs_action_plan_id_action_plans"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], name=op.f("fk_agent_runs_incident_id_incidents"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"], name=op.f("fk_agent_runs_region_id_regions"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["risk_assessment_id"], ["risk_assessments.id"], name=op.f("fk_agent_runs_risk_assessment_id_risk_assessments"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["station_id"], ["sensor_stations.id"], name=op.f("fk_agent_runs_station_id_sensor_stations"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_runs")),
    )
    op.create_index(op.f("ix_agent_runs_action_plan_id"), "agent_runs", ["action_plan_id"], unique=False)
    op.create_index(op.f("ix_agent_runs_incident_id"), "agent_runs", ["incident_id"], unique=False)
    op.create_index(op.f("ix_agent_runs_region_id"), "agent_runs", ["region_id"], unique=False)
    op.create_index(op.f("ix_agent_runs_risk_assessment_id"), "agent_runs", ["risk_assessment_id"], unique=False)
    op.create_index(op.f("ix_agent_runs_run_type"), "agent_runs", ["run_type"], unique=False)
    op.create_index(op.f("ix_agent_runs_started_at"), "agent_runs", ["started_at"], unique=False)
    op.create_index(op.f("ix_agent_runs_station_id"), "agent_runs", ["station_id"], unique=False)
    op.create_index(op.f("ix_agent_runs_status"), "agent_runs", ["status"], unique=False)
    op.create_index(op.f("ix_agent_runs_trigger_source"), "agent_runs", ["trigger_source"], unique=False)
    op.create_index(op.f("ix_agent_runs_finished_at"), "agent_runs", ["finished_at"], unique=False)

    op.create_table(
        "observation_snapshots",
        sa.Column("agent_run_id", sa.UUID(), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("region_id", sa.UUID(), nullable=True),
        sa.Column("station_id", sa.UUID(), nullable=True),
        sa.Column("reading_id", sa.UUID(), nullable=True),
        sa.Column("weather_snapshot_id", sa.UUID(), nullable=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"], name=op.f("fk_observation_snapshots_agent_run_id_agent_runs"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reading_id"], ["sensor_readings.id"], name=op.f("fk_observation_snapshots_reading_id_sensor_readings"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"], name=op.f("fk_observation_snapshots_region_id_regions"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["station_id"], ["sensor_stations.id"], name=op.f("fk_observation_snapshots_station_id_sensor_stations"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["weather_snapshot_id"], ["weather_snapshots.id"], name=op.f("fk_observation_snapshots_weather_snapshot_id_weather_snapshots"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_observation_snapshots")),
        sa.UniqueConstraint("agent_run_id", name=op.f("uq_observation_snapshots_agent_run_id")),
    )
    op.create_index(op.f("ix_observation_snapshots_agent_run_id"), "observation_snapshots", ["agent_run_id"], unique=True)
    op.create_index(op.f("ix_observation_snapshots_captured_at"), "observation_snapshots", ["captured_at"], unique=False)
    op.create_index(op.f("ix_observation_snapshots_reading_id"), "observation_snapshots", ["reading_id"], unique=False)
    op.create_index(op.f("ix_observation_snapshots_region_id"), "observation_snapshots", ["region_id"], unique=False)
    op.create_index(op.f("ix_observation_snapshots_source"), "observation_snapshots", ["source"], unique=False)
    op.create_index(op.f("ix_observation_snapshots_station_id"), "observation_snapshots", ["station_id"], unique=False)
    op.create_index(op.f("ix_observation_snapshots_weather_snapshot_id"), "observation_snapshots", ["weather_snapshot_id"], unique=False)


def downgrade() -> None:
    """Drop run trace and observation snapshot tables."""
    op.drop_index(op.f("ix_observation_snapshots_weather_snapshot_id"), table_name="observation_snapshots")
    op.drop_index(op.f("ix_observation_snapshots_station_id"), table_name="observation_snapshots")
    op.drop_index(op.f("ix_observation_snapshots_source"), table_name="observation_snapshots")
    op.drop_index(op.f("ix_observation_snapshots_region_id"), table_name="observation_snapshots")
    op.drop_index(op.f("ix_observation_snapshots_reading_id"), table_name="observation_snapshots")
    op.drop_index(op.f("ix_observation_snapshots_captured_at"), table_name="observation_snapshots")
    op.drop_index(op.f("ix_observation_snapshots_agent_run_id"), table_name="observation_snapshots")
    op.drop_table("observation_snapshots")

    op.drop_index(op.f("ix_agent_runs_finished_at"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_trigger_source"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_status"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_station_id"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_started_at"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_run_type"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_risk_assessment_id"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_region_id"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_incident_id"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_action_plan_id"), table_name="agent_runs")
    op.drop_table("agent_runs")
