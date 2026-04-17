"""execution jobs alias views

Revision ID: 0011_execution_jobs_alias
Revises: 0010_domain_events_stream
Create Date: 2026-04-17 10:25:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0011_execution_jobs_alias"
down_revision: str | None = "0010_domain_events_stream"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Create execution_jobs aliases without rewriting existing execution tables."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "execution_batches" not in inspector.get_table_names():
        return

    op.execute(
        sa.text(
            """
            CREATE OR REPLACE VIEW execution_jobs AS
            SELECT
                eb.id,
                eb.plan_id,
                eb.region_id,
                eb.status,
                eb.simulated,
                eb.started_at,
                eb.completed_at,
                eb.idempotency_key,
                eb.requested_by,
                eb.created_at,
                eb.updated_at,
                eb.id AS execution_job_id,
                eb.status AS execution_job_status,
                eb.started_at AS execution_job_started_at,
                eb.completed_at AS execution_job_completed_at
            FROM execution_batches eb
            """
        )
    )

    if "action_executions" not in inspector.get_table_names():
        return

    op.execute(
        sa.text(
            """
            CREATE OR REPLACE VIEW execution_job_steps AS
            SELECT
                ae.id,
                ae.plan_id,
                ae.batch_id,
                ae.region_id,
                ae.action_type,
                ae.status,
                ae.simulated,
                ae.step_index,
                ae.started_at,
                ae.completed_at,
                ae.result_summary,
                ae.result_payload,
                ae.idempotency_key,
                ae.requested_by,
                ae.created_at,
                ae.updated_at,
                ae.batch_id AS execution_job_id
            FROM action_executions ae
            """
        )
    )


def downgrade() -> None:
    """Drop execution job alias views."""
    op.execute(sa.text("DROP VIEW IF EXISTS execution_job_steps"))
    op.execute(sa.text("DROP VIEW IF EXISTS execution_jobs"))
