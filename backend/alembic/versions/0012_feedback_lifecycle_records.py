"""feedback lifecycle records

Revision ID: 0012_feedback_lifecycle_records
Revises: 0011_execution_jobs_alias
Create Date: 2026-04-17 11:10:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0012_feedback_lifecycle_records"
down_revision: str | None = "0011_execution_jobs_alias"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Create feedback snapshots and outcome evaluation persistence tables."""
    op.create_table(
        "feedback_snapshots",
        sa.Column("batch_id", sa.UUID(), nullable=False),
        sa.Column("plan_id", sa.UUID(), nullable=False),
        sa.Column("execution_id", sa.UUID(), nullable=True),
        sa.Column("risk_assessment_id", sa.UUID(), nullable=True),
        sa.Column("station_id", sa.UUID(), nullable=True),
        sa.Column("reading_id", sa.UUID(), nullable=True),
        sa.Column("snapshot_kind", sa.String(length=20), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reading_recorded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("salinity_dsm", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("water_level_m", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["execution_batches.id"], name=op.f("fk_feedback_snapshots_batch_id_execution_batches"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["action_plans.id"], name=op.f("fk_feedback_snapshots_plan_id_action_plans"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["execution_id"], ["action_executions.id"], name=op.f("fk_feedback_snapshots_execution_id_action_executions"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["risk_assessment_id"], ["risk_assessments.id"], name=op.f("fk_feedback_snapshots_risk_assessment_id_risk_assessments"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["station_id"], ["sensor_stations.id"], name=op.f("fk_feedback_snapshots_station_id_sensor_stations"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reading_id"], ["sensor_readings.id"], name=op.f("fk_feedback_snapshots_reading_id_sensor_readings"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_feedback_snapshots")),
    )
    op.create_index(op.f("ix_feedback_snapshots_batch_id"), "feedback_snapshots", ["batch_id"], unique=False)
    op.create_index(op.f("ix_feedback_snapshots_plan_id"), "feedback_snapshots", ["plan_id"], unique=False)
    op.create_index(op.f("ix_feedback_snapshots_execution_id"), "feedback_snapshots", ["execution_id"], unique=False)
    op.create_index(op.f("ix_feedback_snapshots_risk_assessment_id"), "feedback_snapshots", ["risk_assessment_id"], unique=False)
    op.create_index(op.f("ix_feedback_snapshots_station_id"), "feedback_snapshots", ["station_id"], unique=False)
    op.create_index(op.f("ix_feedback_snapshots_reading_id"), "feedback_snapshots", ["reading_id"], unique=False)
    op.create_index(op.f("ix_feedback_snapshots_snapshot_kind"), "feedback_snapshots", ["snapshot_kind"], unique=False)
    op.create_index(op.f("ix_feedback_snapshots_captured_at"), "feedback_snapshots", ["captured_at"], unique=False)

    op.create_table(
        "outcome_evaluations",
        sa.Column("batch_id", sa.UUID(), nullable=False),
        sa.Column("plan_id", sa.UUID(), nullable=False),
        sa.Column("execution_id", sa.UUID(), nullable=True),
        sa.Column("before_snapshot_id", sa.UUID(), nullable=True),
        sa.Column("after_snapshot_id", sa.UUID(), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("outcome_class", sa.String(length=50), nullable=False),
        sa.Column("status_legacy", sa.String(length=100), nullable=False),
        sa.Column("baseline_salinity_dsm", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("latest_salinity_dsm", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("delta_dsm", sa.Numeric(precision=7, scale=2), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("replan_recommended", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("replan_reason", sa.Text(), nullable=True),
        sa.Column("evaluator_name", sa.String(length=255), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["execution_batches.id"], name=op.f("fk_outcome_evaluations_batch_id_execution_batches"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["action_plans.id"], name=op.f("fk_outcome_evaluations_plan_id_action_plans"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["execution_id"], ["action_executions.id"], name=op.f("fk_outcome_evaluations_execution_id_action_executions"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["before_snapshot_id"], ["feedback_snapshots.id"], name=op.f("fk_outcome_evaluations_before_snapshot_id_feedback_snapshots"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["after_snapshot_id"], ["feedback_snapshots.id"], name=op.f("fk_outcome_evaluations_after_snapshot_id_feedback_snapshots"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_outcome_evaluations")),
    )
    op.create_index(op.f("ix_outcome_evaluations_batch_id"), "outcome_evaluations", ["batch_id"], unique=False)
    op.create_index(op.f("ix_outcome_evaluations_plan_id"), "outcome_evaluations", ["plan_id"], unique=False)
    op.create_index(op.f("ix_outcome_evaluations_execution_id"), "outcome_evaluations", ["execution_id"], unique=False)
    op.create_index(op.f("ix_outcome_evaluations_before_snapshot_id"), "outcome_evaluations", ["before_snapshot_id"], unique=False)
    op.create_index(op.f("ix_outcome_evaluations_after_snapshot_id"), "outcome_evaluations", ["after_snapshot_id"], unique=False)
    op.create_index(op.f("ix_outcome_evaluations_evaluated_at"), "outcome_evaluations", ["evaluated_at"], unique=False)
    op.create_index(op.f("ix_outcome_evaluations_outcome_class"), "outcome_evaluations", ["outcome_class"], unique=False)

    op.alter_column("outcome_evaluations", "replan_recommended", server_default=None)


def downgrade() -> None:
    """Drop outcome evaluation and feedback snapshot tables."""
    op.drop_index(op.f("ix_outcome_evaluations_outcome_class"), table_name="outcome_evaluations")
    op.drop_index(op.f("ix_outcome_evaluations_evaluated_at"), table_name="outcome_evaluations")
    op.drop_index(op.f("ix_outcome_evaluations_after_snapshot_id"), table_name="outcome_evaluations")
    op.drop_index(op.f("ix_outcome_evaluations_before_snapshot_id"), table_name="outcome_evaluations")
    op.drop_index(op.f("ix_outcome_evaluations_execution_id"), table_name="outcome_evaluations")
    op.drop_index(op.f("ix_outcome_evaluations_plan_id"), table_name="outcome_evaluations")
    op.drop_index(op.f("ix_outcome_evaluations_batch_id"), table_name="outcome_evaluations")
    op.drop_table("outcome_evaluations")

    op.drop_index(op.f("ix_feedback_snapshots_captured_at"), table_name="feedback_snapshots")
    op.drop_index(op.f("ix_feedback_snapshots_snapshot_kind"), table_name="feedback_snapshots")
    op.drop_index(op.f("ix_feedback_snapshots_reading_id"), table_name="feedback_snapshots")
    op.drop_index(op.f("ix_feedback_snapshots_station_id"), table_name="feedback_snapshots")
    op.drop_index(op.f("ix_feedback_snapshots_risk_assessment_id"), table_name="feedback_snapshots")
    op.drop_index(op.f("ix_feedback_snapshots_execution_id"), table_name="feedback_snapshots")
    op.drop_index(op.f("ix_feedback_snapshots_plan_id"), table_name="feedback_snapshots")
    op.drop_index(op.f("ix_feedback_snapshots_batch_id"), table_name="feedback_snapshots")
    op.drop_table("feedback_snapshots")
