"""Source registry-driven sync workflow for static corpus ingestion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.rag.ingestion_service import IngestionResult, ingest_knowledge_file_to_vertex


@dataclass(slots=True)
class SourceSyncRequest:
    """Input contract for registry-driven source synchronization."""

    file_path: str
    title: str | None = None
    source_uri: str | None = None
    source_key: str | None = None
    effective_date: str | None = None
    document_type: str = "guideline"
    tags: list[str] | None = None
    metadata_payload: dict[str, Any] | None = None
    chunk_size: int = 900
    chunk_overlap: int = 120
    force_reindex: bool = False


async def sync_knowledge_source(
    session: AsyncSession,
    *,
    request: SourceSyncRequest,
) -> IngestionResult:
    """Execute the registry/sync workflow for one static knowledge source."""
    return await ingest_knowledge_file_to_vertex(
        session,
        file_path=request.file_path,
        title=request.title,
        source_uri=request.source_uri,
        source_key=request.source_key,
        effective_date=request.effective_date,
        document_type=request.document_type,
        tags=request.tags,
        metadata_payload=request.metadata_payload,
        chunk_size=request.chunk_size,
        chunk_overlap=request.chunk_overlap,
        force_reindex=request.force_reindex,
    )
