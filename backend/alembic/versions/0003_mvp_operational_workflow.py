"""mvp operational workflow

Revision ID: 0003_mvp_operational_workflow
Revises: dbc5b8693c76
Create Date: 2026-04-14 22:00:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003_mvp_operational_workflow"
down_revision: str | None = "dbc5b8693c76"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Add auth, incidents, approvals, execution audit, and notifications."""
    op.execute("ALTER TYPE action_plan_status ADD VALUE IF NOT EXISTS 'pending_approval'")
    op.execute("ALTER TYPE action_plan_status ADD VALUE IF NOT EXISTS 'approved'")
    op.execute("ALTER TYPE action_plan_status ADD VALUE IF NOT EXISTS 'rejected'")
    op.execute("ALTER TYPE action_type ADD VALUE IF NOT EXISTS 'close_gate'")
    op.execute("ALTER TYPE action_type ADD VALUE IF NOT EXISTS 'open_gate'")
    op.execute("ALTER TYPE action_type ADD VALUE IF NOT EXISTS 'start_pump'")
    op.execute("ALTER TYPE action_type ADD VALUE IF NOT EXISTS 'stop_pump'")
    op.execute("ALTER TYPE action_type ADD VALUE IF NOT EXISTS 'send_alert'")

    user_role = sa.Enum("admin", "supervisor", "operator", "viewer", name="user_role")
    incident_status = sa.Enum(
        "open",
        "investigating",
        "pending_plan",
        "pending_approval",
        "approved",
        "executing",
        "resolved",
        "closed",
        name="incident_status",
    )
    incident_severity = sa.Enum(
        "safe",
        "warning",
        "danger",
        "critical",
        name="incident_severity",
    )
    approval_decision = sa.Enum("approved", "rejected", name="approval_decision")
    notification_channel = sa.Enum(
        "dashboard",
        "sms_mock",
        "zalo_mock",
        "email_mock",
        name="notification_channel",
    )
    notification_status = sa.Enum("pending", "sent", "failed", name="notification_status")
    audit_event_type = sa.Enum(
        "auth",
        "ingestion",
        "risk",
        "incident",
        "plan",
        "approval",
        "execution",
        "notification",
        "knowledge",
        name="audit_event_type",
    )

    op.create_table(
        "users",
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("role", user_role, nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    op.add_column("sensor_readings", sa.Column("wind_speed_mps", sa.Numeric(precision=6, scale=2), nullable=True))
    op.add_column("sensor_readings", sa.Column("wind_direction_deg", sa.Integer(), nullable=True))
    op.add_column("sensor_readings", sa.Column("flow_rate_m3s", sa.Numeric(precision=8, scale=3), nullable=True))
    op.add_column(
        "sensor_readings",
        sa.Column("source", sa.String(length=100), server_default="simulator", nullable=False),
    )

    op.create_table(
        "incidents",
        sa.Column("region_id", sa.UUID(), nullable=False),
        sa.Column("station_id", sa.UUID(), nullable=True),
        sa.Column("risk_assessment_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", incident_severity, nullable=False),
        sa.Column("status", incident_status, nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=255), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"], name=op.f("fk_incidents_region_id_regions"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["risk_assessment_id"], ["risk_assessments.id"], name=op.f("fk_incidents_risk_assessment_id_risk_assessments"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["station_id"], ["sensor_stations.id"], name=op.f("fk_incidents_station_id_sensor_stations"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_incidents")),
    )
    op.create_index(op.f("ix_incidents_opened_at"), "incidents", ["opened_at"], unique=False)
    op.create_index(op.f("ix_incidents_region_id"), "incidents", ["region_id"], unique=False)
    op.create_index(op.f("ix_incidents_risk_assessment_id"), "incidents", ["risk_assessment_id"], unique=False)
    op.create_index(op.f("ix_incidents_severity"), "incidents", ["severity"], unique=False)
    op.create_index(op.f("ix_incidents_station_id"), "incidents", ["station_id"], unique=False)
    op.create_index(op.f("ix_incidents_status"), "incidents", ["status"], unique=False)

    op.add_column("action_plans", sa.Column("incident_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        op.f("fk_action_plans_incident_id_incidents"),
        "action_plans",
        "incidents",
        ["incident_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_action_plans_incident_id"), "action_plans", ["incident_id"], unique=False)

    op.add_column("action_executions", sa.Column("idempotency_key", sa.String(length=120), nullable=True))
    op.add_column("action_executions", sa.Column("requested_by", sa.String(length=255), nullable=True))
    op.create_unique_constraint(op.f("uq_action_executions_idempotency_key"), "action_executions", ["idempotency_key"])

    op.create_table(
        "approvals",
        sa.Column("plan_id", sa.UUID(), nullable=False),
        sa.Column("decided_by_user_id", sa.UUID(), nullable=True),
        sa.Column("decided_by_name", sa.String(length=255), nullable=False),
        sa.Column("decision", approval_decision, nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["decided_by_user_id"], ["users.id"], name=op.f("fk_approvals_decided_by_user_id_users"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["plan_id"], ["action_plans.id"], name=op.f("fk_approvals_plan_id_action_plans"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_approvals")),
    )
    op.create_index(op.f("ix_approvals_decided_at"), "approvals", ["decided_at"], unique=False)
    op.create_index(op.f("ix_approvals_decided_by_user_id"), "approvals", ["decided_by_user_id"], unique=False)
    op.create_index(op.f("ix_approvals_decision"), "approvals", ["decision"], unique=False)
    op.create_index(op.f("ix_approvals_plan_id"), "approvals", ["plan_id"], unique=False)

    op.create_table(
        "notifications",
        sa.Column("incident_id", sa.UUID(), nullable=True),
        sa.Column("execution_id", sa.UUID(), nullable=True),
        sa.Column("channel", notification_channel, nullable=False),
        sa.Column("status", notification_status, nullable=False),
        sa.Column("recipient", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["execution_id"], ["action_executions.id"], name=op.f("fk_notifications_execution_id_action_executions"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], name=op.f("fk_notifications_incident_id_incidents"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_notifications")),
    )
    op.create_index(op.f("ix_notifications_channel"), "notifications", ["channel"], unique=False)
    op.create_index(op.f("ix_notifications_execution_id"), "notifications", ["execution_id"], unique=False)
    op.create_index(op.f("ix_notifications_incident_id"), "notifications", ["incident_id"], unique=False)
    op.create_index(op.f("ix_notifications_status"), "notifications", ["status"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("event_type", audit_event_type, nullable=False),
        sa.Column("actor_name", sa.String(length=255), nullable=False),
        sa.Column("actor_role", sa.String(length=50), nullable=True),
        sa.Column("region_id", sa.UUID(), nullable=True),
        sa.Column("incident_id", sa.UUID(), nullable=True),
        sa.Column("action_plan_id", sa.UUID(), nullable=True),
        sa.Column("action_execution_id", sa.UUID(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["action_execution_id"], ["action_executions.id"], name=op.f("fk_audit_logs_action_execution_id_action_executions"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["action_plan_id"], ["action_plans.id"], name=op.f("fk_audit_logs_action_plan_id_action_plans"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], name=op.f("fk_audit_logs_incident_id_incidents"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"], name=op.f("fk_audit_logs_region_id_regions"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_logs")),
    )
    op.create_index(op.f("ix_audit_logs_action_execution_id"), "audit_logs", ["action_execution_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_action_plan_id"), "audit_logs", ["action_plan_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_event_type"), "audit_logs", ["event_type"], unique=False)
    op.create_index(op.f("ix_audit_logs_incident_id"), "audit_logs", ["incident_id"], unique=False)
    op.create_index(op.f("ix_audit_logs_occurred_at"), "audit_logs", ["occurred_at"], unique=False)
    op.create_index(op.f("ix_audit_logs_region_id"), "audit_logs", ["region_id"], unique=False)

    op.create_table(
        "action_outcomes",
        sa.Column("execution_id", sa.UUID(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("pre_metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("post_metrics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(length=100), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["execution_id"], ["action_executions.id"], name=op.f("fk_action_outcomes_execution_id_action_executions"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_action_outcomes")),
    )
    op.create_index(op.f("ix_action_outcomes_execution_id"), "action_outcomes", ["execution_id"], unique=False)
    op.create_index(op.f("ix_action_outcomes_recorded_at"), "action_outcomes", ["recorded_at"], unique=False)


def downgrade() -> None:
    """Drop MVP workflow tables and columns."""
    op.drop_index(op.f("ix_action_outcomes_recorded_at"), table_name="action_outcomes")
    op.drop_index(op.f("ix_action_outcomes_execution_id"), table_name="action_outcomes")
    op.drop_table("action_outcomes")
    op.drop_index(op.f("ix_audit_logs_region_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_occurred_at"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_incident_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_event_type"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action_plan_id"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action_execution_id"), table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index(op.f("ix_notifications_status"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_incident_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_execution_id"), table_name="notifications")
    op.drop_index(op.f("ix_notifications_channel"), table_name="notifications")
    op.drop_table("notifications")
    op.drop_index(op.f("ix_approvals_plan_id"), table_name="approvals")
    op.drop_index(op.f("ix_approvals_decision"), table_name="approvals")
    op.drop_index(op.f("ix_approvals_decided_by_user_id"), table_name="approvals")
    op.drop_index(op.f("ix_approvals_decided_at"), table_name="approvals")
    op.drop_table("approvals")
    op.drop_constraint(op.f("uq_action_executions_idempotency_key"), "action_executions", type_="unique")
    op.drop_column("action_executions", "requested_by")
    op.drop_column("action_executions", "idempotency_key")
    op.drop_index(op.f("ix_action_plans_incident_id"), table_name="action_plans")
    op.drop_constraint(op.f("fk_action_plans_incident_id_incidents"), "action_plans", type_="foreignkey")
    op.drop_column("action_plans", "incident_id")
    op.drop_index(op.f("ix_incidents_status"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_station_id"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_severity"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_risk_assessment_id"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_region_id"), table_name="incidents")
    op.drop_index(op.f("ix_incidents_opened_at"), table_name="incidents")
    op.drop_table("incidents")
    op.drop_column("sensor_readings", "source")
    op.drop_column("sensor_readings", "flow_rate_m3s")
    op.drop_column("sensor_readings", "wind_direction_deg")
    op.drop_column("sensor_readings", "wind_speed_mps")
    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_role"), table_name="users")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS audit_event_type")
    op.execute("DROP TYPE IF EXISTS notification_status")
    op.execute("DROP TYPE IF EXISTS notification_channel")
    op.execute("DROP TYPE IF EXISTS approval_decision")
    op.execute("DROP TYPE IF EXISTS incident_severity")
    op.execute("DROP TYPE IF EXISTS incident_status")
    op.execute("DROP TYPE IF EXISTS user_role")
