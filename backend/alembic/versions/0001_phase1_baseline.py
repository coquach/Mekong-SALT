"""phase 1 baseline

Revision ID: 0001_phase1_baseline
Revises:
Create Date: 2026-03-27 23:59:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0001_phase1_baseline"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Enable pgvector for later vector-backed knowledge memory."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    """Remove the pgvector extension."""
    op.execute("DROP EXTENSION IF EXISTS vector")

