"""knowledge registry explicit source/provider fields

Revision ID: 0013_knowledge_registry_fields
Revises: 0012_feedback_lifecycle_records
Create Date: 2026-04-17 15:20:00
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0013_knowledge_registry_fields"
down_revision: str | None = "0012_feedback_lifecycle_records"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    """Add explicit source-of-truth registry and provider sync columns."""
    op.add_column("knowledge_documents", sa.Column("source_key", sa.String(length=255), nullable=True))
    op.add_column("knowledge_documents", sa.Column("effective_date", sa.Date(), nullable=True))
    op.add_column("knowledge_documents", sa.Column("content_sha256", sa.String(length=64), nullable=True))
    op.add_column(
        "knowledge_documents",
        sa.Column("document_version", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column("knowledge_documents", sa.Column("index_provider", sa.String(length=100), nullable=True))
    op.add_column("knowledge_documents", sa.Column("provider_document_id", sa.String(length=255), nullable=True))
    op.add_column(
        "knowledge_documents",
        sa.Column("provider_sync_status", sa.String(length=50), nullable=True, server_default="pending"),
    )
    op.add_column("knowledge_documents", sa.Column("provider_synced_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("knowledge_documents", sa.Column("provider_error", sa.Text(), nullable=True))
    op.add_column("knowledge_documents", sa.Column("last_indexed_at", sa.DateTime(timezone=True), nullable=True))

    op.create_index(op.f("ix_knowledge_documents_source_key"), "knowledge_documents", ["source_key"], unique=False)
    op.create_index(
        op.f("ix_knowledge_documents_effective_date"),
        "knowledge_documents",
        ["effective_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_documents_provider_sync_status"),
        "knowledge_documents",
        ["provider_sync_status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_knowledge_documents_last_indexed_at"),
        "knowledge_documents",
        ["last_indexed_at"],
        unique=False,
    )

    op.alter_column("knowledge_documents", "document_version", server_default=None)
    op.alter_column("knowledge_documents", "provider_sync_status", server_default=None)


def downgrade() -> None:
    """Remove explicit source/provider registry columns."""
    op.drop_index(op.f("ix_knowledge_documents_last_indexed_at"), table_name="knowledge_documents")
    op.drop_index(op.f("ix_knowledge_documents_provider_sync_status"), table_name="knowledge_documents")
    op.drop_index(op.f("ix_knowledge_documents_effective_date"), table_name="knowledge_documents")
    op.drop_index(op.f("ix_knowledge_documents_source_key"), table_name="knowledge_documents")

    op.drop_column("knowledge_documents", "last_indexed_at")
    op.drop_column("knowledge_documents", "provider_error")
    op.drop_column("knowledge_documents", "provider_synced_at")
    op.drop_column("knowledge_documents", "provider_sync_status")
    op.drop_column("knowledge_documents", "provider_document_id")
    op.drop_column("knowledge_documents", "index_provider")
    op.drop_column("knowledge_documents", "document_version")
    op.drop_column("knowledge_documents", "content_sha256")
    op.drop_column("knowledge_documents", "effective_date")
    op.drop_column("knowledge_documents", "source_key")
