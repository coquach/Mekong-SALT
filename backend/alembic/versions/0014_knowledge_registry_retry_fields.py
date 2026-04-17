"""knowledge registry retry metadata fields

Revision ID: 0014_registry_retry_meta
Revises: 0013_knowledge_registry_fields
Create Date: 2026-04-17 15:55:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0014_registry_retry_meta"
down_revision: str | None = "0013_knowledge_registry_fields"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Add retry metadata columns for provider sync lifecycle."""
    op.add_column(
        "knowledge_documents",
        sa.Column("provider_retry_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "knowledge_documents",
        sa.Column("provider_last_retry_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.alter_column("knowledge_documents", "provider_retry_count", server_default=None)


def downgrade() -> None:
    """Remove retry metadata columns from provider sync lifecycle."""
    op.drop_column("knowledge_documents", "provider_last_retry_at")
    op.drop_column("knowledge_documents", "provider_retry_count")
