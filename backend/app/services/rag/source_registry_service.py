"""Source registry lifecycle service for static corpus synchronization."""

from __future__ import annotations

from datetime import UTC, datetime

from app.models.knowledge import KnowledgeDocument


class SourceRegistrySyncStatus:
    """Known source registry sync lifecycle values."""

    PENDING = "pending"
    SYNCING = "syncing"
    SYNCED = "synced"
    FAILED = "failed"


class SourceRegistryService:
    """Manage explicit lifecycle state for static corpus source records."""

    def mark_syncing(
        self,
        document: KnowledgeDocument,
        *,
        at: datetime,
    ) -> None:
        """Mark the document as currently syncing to provider."""
        document.provider_sync_status = SourceRegistrySyncStatus.SYNCING
        document.provider_error = None
        document.last_indexed_at = at

    def mark_synced(
        self,
        document: KnowledgeDocument,
        *,
        provider_document_id: str,
        at: datetime,
    ) -> None:
        """Mark successful provider synchronization."""
        document.provider_document_id = provider_document_id
        document.provider_sync_status = SourceRegistrySyncStatus.SYNCED
        document.provider_synced_at = at
        document.provider_error = None

    def mark_failed(
        self,
        document: KnowledgeDocument,
        *,
        error_message: str,
        at: datetime,
    ) -> None:
        """Mark failed provider synchronization and capture retry metadata."""
        document.provider_sync_status = SourceRegistrySyncStatus.FAILED
        document.provider_error = error_message.strip()[:2000]
        document.provider_retry_count = int(document.provider_retry_count or 0) + 1
        document.provider_last_retry_at = at.astimezone(UTC)
