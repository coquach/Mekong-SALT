"""Ingestion service for document/csv knowledge into Vertex Vector Search."""

from __future__ import annotations

import csv
import hashlib
import importlib
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.models.knowledge import EmbeddedChunk, KnowledgeDocument
from app.repositories.knowledge import KnowledgeDocumentRepository
from app.services.rag.static_corpus_provider import get_static_corpus_provider
from app.services.rag.vertex_vector_search_service import VertexVectorSearchService


@dataclass(slots=True)
class IngestionResult:
    """Summary of one ingestion operation."""

    document_id: str
    chunk_count: int
    source_uri: str | None
    version: int = 1
    reindexed: bool = False
    skipped: bool = False


async def ingest_knowledge_file_to_vertex(
    session: AsyncSession,
    *,
    file_path: str,
    title: str | None = None,
    source_uri: str | None = None,
    source_key: str | None = None,
    effective_date: str | None = None,
    document_type: str = "guideline",
    tags: list[str] | None = None,
    metadata_payload: dict[str, Any] | None = None,
    chunk_size: int = 900,
    chunk_overlap: int = 120,
    force_reindex: bool = False,
) -> IngestionResult:
    """Ingest txt/md/csv/docx content and upsert vectors to Vertex Vector Search."""
    settings = get_settings()
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        raise AppException(
            status_code=404,
            code="rag_ingest_file_not_found",
            message=f"Knowledge source '{file_path}' was not found.",
        )

    content = _load_content(path)
    if not content.strip():
        raise AppException(
            status_code=400,
            code="rag_ingest_empty_content",
            message="Knowledge source has no readable content.",
        )

    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    now = datetime.now(UTC)
    base_tags = list(tags or [])
    ext = path.suffix.lower()
    if ext == ".csv" and "csv" not in base_tags:
        base_tags.append("csv")

    repository = KnowledgeDocumentRepository(session)
    existing_document = (
        await repository.get_by_source_uri(source_uri)
        if source_uri
        else None
    )
    existing_metadata = (
        dict(existing_document.metadata_payload or {})
        if existing_document is not None
        else {}
    )

    if existing_document is not None:
        # Backfill legacy metadata contract from explicit registry columns when available.
        if existing_document.content_sha256:
            existing_metadata.setdefault("content_sha256", existing_document.content_sha256)
        if existing_document.last_indexed_at is not None:
            existing_metadata.setdefault("last_indexed_at", existing_document.last_indexed_at.isoformat())
        if existing_document.document_version is not None:
            existing_metadata.setdefault("document_version", existing_document.document_version)
        if existing_document.source_key:
            existing_metadata.setdefault("source_key", existing_document.source_key)
        if existing_document.effective_date is not None:
            existing_metadata.setdefault("effective_date", existing_document.effective_date.isoformat())

    resolved_source_key = source_key or str(
        (metadata_payload or {}).get("source_key")
        or existing_metadata.get("source_key")
        or source_uri
        or path.stem
    )
    resolved_effective_date = _resolve_effective_date(
        path=path,
        explicit_effective_date=effective_date,
        existing_metadata=existing_metadata,
    )

    should_reindex = force_reindex
    if existing_document is not None and not force_reindex:
        should_reindex = _should_reindex_existing(
            ext=ext,
            existing_metadata=existing_metadata,
            content_hash=content_hash,
            now=now,
            csv_ttl_days=settings.rag_csv_reindex_ttl_days,
        )

    if existing_document is not None and not should_reindex:
        chunk_count = await repository.count_chunks_for_document(existing_document.id)
        return IngestionResult(
            document_id=str(existing_document.id),
            chunk_count=chunk_count,
            source_uri=existing_document.source_uri,
            version=int(existing_metadata.get("document_version") or 1),
            reindexed=False,
            skipped=True,
        )

    version_history = list(existing_metadata.get("version_history") or [])
    document_version = int(existing_metadata.get("document_version") or 0)
    if existing_document is not None:
        document_version += 1
        previous_entry = {
            "version": document_version - 1,
            "effective_date": existing_metadata.get("effective_date"),
            "content_sha256": existing_metadata.get("content_sha256"),
            "last_indexed_at": existing_metadata.get("last_indexed_at"),
        }
        version_history.append(previous_entry)
        version_history = version_history[-20:]
    else:
        document_version = 1

    merged_metadata: dict[str, Any] = {
        **existing_metadata,
        **(metadata_payload or {}),
        "file_name": path.name,
        "file_extension": ext,
        "source_key": resolved_source_key,
        "effective_date": resolved_effective_date,
        "document_version": document_version,
        "content_sha256": content_hash,
        "file_last_modified_at": datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat(),
        "last_indexed_at": now.isoformat(),
        "index_provider": "vertex_vector_search",
        "version_history": version_history,
    }

    vector_service = VertexVectorSearchService()
    static_provider = get_static_corpus_provider(vector_service=vector_service)
    if existing_document is not None:
        old_chunk_ids = await repository.list_chunk_ids_for_document(existing_document.id)
        if old_chunk_ids:
            await static_provider.remove_datapoints([str(item) for item in old_chunk_ids])
        await repository.delete_chunks_for_document(existing_document.id)

        existing_document.title = title or path.stem
        existing_document.document_type = document_type
        existing_document.summary = _summarize_for_document(content)
        existing_document.content_text = content
        existing_document.tags = base_tags or None
        existing_document.metadata_payload = merged_metadata
        existing_document.source_key = resolved_source_key
        existing_document.effective_date = _parse_effective_date_or_raise(resolved_effective_date)
        existing_document.content_sha256 = content_hash
        existing_document.document_version = document_version
        existing_document.index_provider = "vertex_vector_search"
        existing_document.provider_sync_status = "syncing"
        existing_document.provider_error = None
        existing_document.last_indexed_at = now
        document = existing_document
    else:
        document = KnowledgeDocument(
            title=title or path.stem,
            source_uri=source_uri,
            document_type=document_type,
            summary=_summarize_for_document(content),
            content_text=content,
            tags=base_tags or None,
            metadata_payload=merged_metadata,
            source_key=resolved_source_key,
            effective_date=_parse_effective_date_or_raise(resolved_effective_date),
            content_sha256=content_hash,
            document_version=document_version,
            index_provider="vertex_vector_search",
            provider_sync_status="syncing",
            provider_error=None,
            last_indexed_at=now,
        )
        session.add(document)

    await session.flush()

    chunks = _chunk_text(content, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    if not chunks:
        chunks = [content.strip()]

    vectors = await static_provider.embed_texts(chunks)

    db_chunks: list[EmbeddedChunk] = []
    datapoints: list[dict[str, Any]] = []
    for index, (chunk_text, vector) in enumerate(zip(chunks, vectors, strict=True)):
        chunk = EmbeddedChunk(
            document_id=document.id,
            chunk_index=index,
            content_text=chunk_text,
            token_count=_estimate_token_count(chunk_text),
            embedding=vector,
            metadata_payload={
                "source": "rag_ingestion",
                "document_type": document_type,
                "file_name": path.name,
            },
        )
        session.add(chunk)
        await session.flush()
        db_chunks.append(chunk)

        datapoints.append(
            {
                "datapoint_id": str(chunk.id),
                "feature_vector": vector,
                "restricts": {
                    "document_type": [document_type],
                    "region_scope": [str((metadata_payload or {}).get("region_code") or "global")],
                    "source_key": [resolved_source_key],
                },
            }
        )

    await static_provider.upsert_datapoints(datapoints)

    document.provider_document_id = str(document.id)
    document.provider_sync_status = "synced"
    document.provider_synced_at = datetime.now(UTC)
    document.provider_error = None
    await session.commit()

    return IngestionResult(
        document_id=str(document.id),
        chunk_count=len(db_chunks),
        source_uri=document.source_uri,
        version=document_version,
        reindexed=existing_document is not None,
        skipped=False,
    )


def _resolve_effective_date(
    *,
    path: Path,
    explicit_effective_date: str | None,
    existing_metadata: dict[str, Any],
) -> str:
    if explicit_effective_date:
        return explicit_effective_date
    if existing_metadata.get("effective_date"):
        return str(existing_metadata["effective_date"])
    modified = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).date()
    return modified.isoformat()


def _parse_effective_date_or_raise(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise AppException(
            status_code=400,
            code="rag_ingest_invalid_effective_date",
            message="effective_date must be in ISO format (YYYY-MM-DD).",
        ) from exc


def _should_reindex_existing(
    *,
    ext: str,
    existing_metadata: dict[str, Any],
    content_hash: str,
    now: datetime,
    csv_ttl_days: int,
) -> bool:
    previous_hash = str(existing_metadata.get("content_sha256") or "")
    if previous_hash != content_hash:
        return True

    if ext != ".csv":
        return False

    last_indexed_raw = existing_metadata.get("last_indexed_at")
    if not last_indexed_raw:
        return True
    try:
        last_indexed_at = datetime.fromisoformat(str(last_indexed_raw))
    except ValueError:
        return True

    if last_indexed_at.tzinfo is None:
        last_indexed_at = last_indexed_at.replace(tzinfo=UTC)

    ttl = max(1, int(csv_ttl_days))
    return now >= (last_indexed_at + timedelta(days=ttl))


def _load_content(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".txt", ".md", ".rst", ".json", ".yaml", ".yml", ".log"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if ext == ".csv":
        return _load_csv_content(path)
    if ext == ".docx":
        return _load_docx_content(path)

    raise AppException(
        status_code=400,
        code="rag_ingest_file_type_not_supported",
        message=(
            "Unsupported file type for ingestion. Supported: txt, md, rst, json, "
            "yaml, yml, log, csv, docx."
        ),
    )


def _load_csv_content(path: Path) -> str:
    rows: list[str] = []
    with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        for row_index, row in enumerate(reader, start=1):
            normalized = "; ".join(f"{key}={row.get(key)}" for key in headers)
            rows.append(f"row={row_index}; {normalized}")

    if not rows:
        raw = path.read_text(encoding="utf-8", errors="ignore")
        return raw
    return "\n".join(rows)


def _load_docx_content(path: Path) -> str:
    try:
        document_module = importlib.import_module("docx")
        Document = getattr(document_module, "Document")
    except Exception as exc:  # pragma: no cover - optional dependency
        raise AppException(
            status_code=400,
            code="rag_ingest_docx_dependency_missing",
            message="DOCX ingestion requires python-docx. Install it to ingest .docx files.",
        ) from exc

    document = Document(str(path))
    lines = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
    return "\n".join(lines)


def _chunk_text(text: str, *, chunk_size: int, chunk_overlap: int) -> list[str]:
    clean = " ".join(text.split())
    if not clean:
        return []

    size = max(300, chunk_size)
    overlap = max(0, min(chunk_overlap, size // 2))
    step = max(1, size - overlap)

    chunks: list[str] = []
    start = 0
    while start < len(clean):
        piece = clean[start : start + size].strip()
        if piece:
            chunks.append(piece)
        start += step
    return chunks


def _estimate_token_count(text: str) -> int:
    return max(1, len(text.split()))


def _summarize_for_document(text: str, limit: int = 260) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."
