"""domain events stream

Revision ID: 0010_domain_events_stream
Revises: 0009_memory_cases
Create Date: 2026-04-16 23:20:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0010_domain_events_stream"
down_revision: str | None = "0009_memory_cases"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Create durable domain event stream table for realtime cursor consumers."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("domain_events"):
        op.create_table(
            "domain_events",
            sa.Column("sequence", sa.BigInteger(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column("event_type", sa.String(length=120), nullable=False),
            sa.Column("source", sa.String(length=120), nullable=True),
            sa.Column("aggregate_type", sa.String(length=120), nullable=True),
            sa.Column("aggregate_id", sa.UUID(), nullable=True),
            sa.Column("region_id", sa.UUID(), nullable=True),
            sa.Column("incident_id", sa.UUID(), nullable=True),
            sa.Column("action_plan_id", sa.UUID(), nullable=True),
            sa.Column("execution_batch_id", sa.UUID(), nullable=True),
            sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        )
    else:
        existing = {column["name"] for column in inspector.get_columns("domain_events")}
        if "sequence" not in existing:
            op.add_column("domain_events", sa.Column("sequence", sa.BigInteger(), nullable=True))
        if "event_type" not in existing:
            op.add_column("domain_events", sa.Column("event_type", sa.String(length=120), nullable=True))
        if "source" not in existing:
            op.add_column("domain_events", sa.Column("source", sa.String(length=120), nullable=True))
        if "aggregate_type" not in existing:
            op.add_column("domain_events", sa.Column("aggregate_type", sa.String(length=120), nullable=True))
        if "aggregate_id" not in existing:
            op.add_column("domain_events", sa.Column("aggregate_id", sa.UUID(), nullable=True))
        if "region_id" not in existing:
            op.add_column("domain_events", sa.Column("region_id", sa.UUID(), nullable=True))
        if "incident_id" not in existing:
            op.add_column("domain_events", sa.Column("incident_id", sa.UUID(), nullable=True))
        if "action_plan_id" not in existing:
            op.add_column("domain_events", sa.Column("action_plan_id", sa.UUID(), nullable=True))
        if "execution_batch_id" not in existing:
            op.add_column("domain_events", sa.Column("execution_batch_id", sa.UUID(), nullable=True))
        if "occurred_at" not in existing:
            op.add_column(
                "domain_events",
                sa.Column(
                    "occurred_at",
                    sa.DateTime(timezone=True),
                    nullable=False,
                    server_default=sa.text("now()"),
                ),
            )
        if "payload" not in existing:
            op.add_column(
                "domain_events",
                sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            )

    existing_indexes = {index["name"] for index in inspector.get_indexes("domain_events")}
    for index_name, column_name in [
        (op.f("ix_domain_events_event_type"), "event_type"),
        (op.f("ix_domain_events_occurred_at"), "occurred_at"),
        (op.f("ix_domain_events_incident_id"), "incident_id"),
        (op.f("ix_domain_events_action_plan_id"), "action_plan_id"),
        (op.f("ix_domain_events_execution_batch_id"), "execution_batch_id"),
    ]:
        if index_name not in existing_indexes:
            op.create_index(index_name, "domain_events", [column_name], unique=False)


def downgrade() -> None:
    """Drop domain event stream table."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("domain_events"):
        for index_name in [
            op.f("ix_domain_events_execution_batch_id"),
            op.f("ix_domain_events_action_plan_id"),
            op.f("ix_domain_events_incident_id"),
            op.f("ix_domain_events_occurred_at"),
            op.f("ix_domain_events_event_type"),
        ]:
            if index_name in {index["name"] for index in inspector.get_indexes("domain_events")}:
                op.drop_index(index_name, table_name="domain_events")
        op.drop_table("domain_events")
