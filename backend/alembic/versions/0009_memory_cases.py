"""memory cases table for context-action-outcome reuse

Revision ID: 0009_memory_cases
Revises: 0008_execution_batches
Create Date: 2026-04-16 20:30:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0009_memory_cases"
down_revision: str | None = "0008_execution_batches"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Create persistent memory case table for retrieval-time reuse."""
    op.create_table(
        "memory_cases",
        sa.Column("region_id", sa.UUID(), nullable=False),
        sa.Column("station_id", sa.UUID(), nullable=True),
        sa.Column("risk_assessment_id", sa.UUID(), nullable=True),
        sa.Column("incident_id", sa.UUID(), nullable=True),
        sa.Column("action_plan_id", sa.UUID(), nullable=True),
        sa.Column("action_execution_id", sa.UUID(), nullable=True),
        sa.Column("decision_log_id", sa.UUID(), nullable=True),
        sa.Column("objective", sa.String(length=255), nullable=True),
        sa.Column("severity", sa.String(length=50), nullable=True),
        sa.Column("outcome_class", sa.String(length=50), nullable=False),
        sa.Column("outcome_status_legacy", sa.String(length=100), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("context_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("action_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("outcome_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("keywords", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"], name=op.f("fk_memory_cases_region_id_regions"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["station_id"], ["sensor_stations.id"], name=op.f("fk_memory_cases_station_id_sensor_stations"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["risk_assessment_id"], ["risk_assessments.id"], name=op.f("fk_memory_cases_risk_assessment_id_risk_assessments"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], name=op.f("fk_memory_cases_incident_id_incidents"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["action_plan_id"], ["action_plans.id"], name=op.f("fk_memory_cases_action_plan_id_action_plans"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["action_execution_id"], ["action_executions.id"], name=op.f("fk_memory_cases_action_execution_id_action_executions"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["decision_log_id"], ["decision_logs.id"], name=op.f("fk_memory_cases_decision_log_id_decision_logs"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_memory_cases")),
    )

    op.create_index(op.f("ix_memory_cases_region_id"), "memory_cases", ["region_id"], unique=False)
    op.create_index(op.f("ix_memory_cases_station_id"), "memory_cases", ["station_id"], unique=False)
    op.create_index(op.f("ix_memory_cases_risk_assessment_id"), "memory_cases", ["risk_assessment_id"], unique=False)
    op.create_index(op.f("ix_memory_cases_incident_id"), "memory_cases", ["incident_id"], unique=False)
    op.create_index(op.f("ix_memory_cases_action_plan_id"), "memory_cases", ["action_plan_id"], unique=False)
    op.create_index(op.f("ix_memory_cases_action_execution_id"), "memory_cases", ["action_execution_id"], unique=False)
    op.create_index(op.f("ix_memory_cases_decision_log_id"), "memory_cases", ["decision_log_id"], unique=False)
    op.create_index(op.f("ix_memory_cases_severity"), "memory_cases", ["severity"], unique=False)
    op.create_index(op.f("ix_memory_cases_outcome_class"), "memory_cases", ["outcome_class"], unique=False)
    op.create_index(op.f("ix_memory_cases_occurred_at"), "memory_cases", ["occurred_at"], unique=False)


def downgrade() -> None:
    """Drop memory case table."""
    op.drop_index(op.f("ix_memory_cases_occurred_at"), table_name="memory_cases")
    op.drop_index(op.f("ix_memory_cases_outcome_class"), table_name="memory_cases")
    op.drop_index(op.f("ix_memory_cases_severity"), table_name="memory_cases")
    op.drop_index(op.f("ix_memory_cases_decision_log_id"), table_name="memory_cases")
    op.drop_index(op.f("ix_memory_cases_action_execution_id"), table_name="memory_cases")
    op.drop_index(op.f("ix_memory_cases_action_plan_id"), table_name="memory_cases")
    op.drop_index(op.f("ix_memory_cases_incident_id"), table_name="memory_cases")
    op.drop_index(op.f("ix_memory_cases_risk_assessment_id"), table_name="memory_cases")
    op.drop_index(op.f("ix_memory_cases_station_id"), table_name="memory_cases")
    op.drop_index(op.f("ix_memory_cases_region_id"), table_name="memory_cases")
    op.drop_table("memory_cases")
