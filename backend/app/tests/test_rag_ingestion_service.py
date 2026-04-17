"""Tests for governance behavior in RAG ingestion service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import hashlib
from pathlib import Path

import pytest

from app.models.knowledge import KnowledgeDocument
from app.repositories.knowledge import KnowledgeDocumentRepository
from app.services.rag.ingestion_service import ingest_knowledge_file_to_vertex


@pytest.mark.asyncio
async def test_csv_ingestion_reindexes_by_ttl_and_tracks_versioning(
    db_session,
    monkeypatch,
    tmp_path: Path,
):
    calls = {
        "upsert": 0,
        "remove": 0,
        "datapoints": [],
    }

    class FakeVectorService:
        async def embed_texts(self, texts: list[str]) -> list[list[float]]:
            return [[0.01] * 768 for _ in texts]

        async def upsert_datapoints(self, datapoints):
            calls["upsert"] += 1
            calls["datapoints"].append(datapoints)

        async def remove_datapoints(self, datapoint_ids):
            if datapoint_ids:
                calls["remove"] += 1

    class FakeSettings:
        rag_csv_reindex_ttl_days = 1

    monkeypatch.setattr(
        "app.services.rag.ingestion_service.VertexVectorSearchService",
        lambda: FakeVectorService(),
    )
    monkeypatch.setattr(
        "app.services.rag.ingestion_service.get_settings",
        lambda: FakeSettings(),
    )

    source_file = tmp_path / "thresholds.csv"
    source_file.write_text(
        "policy_id,warning_threshold_dsm,critical_threshold_dsm\n"
        "POL-001,2.5,4.0\n",
        encoding="utf-8",
    )

    first = await ingest_knowledge_file_to_vertex(
        db_session,
        file_path=str(source_file),
        source_uri="mekong-salt://tests/thresholds",
        source_key="thresholds-tests",
        effective_date="2026-04-01",
        document_type="threshold",
        tags=["threshold", "csv"],
    )

    assert first.version == 1
    assert first.reindexed is False
    assert first.skipped is False
    assert calls["upsert"] == 1
    assert calls["datapoints"]
    first_batch = calls["datapoints"][0]
    assert first_batch
    assert first_batch[0]["restricts"]["entity_type"] == ["knowledge_document"]

    repo = KnowledgeDocumentRepository(db_session)
    document = await repo.get_by_source_uri("mekong-salt://tests/thresholds")
    assert document is not None
    metadata = dict(document.metadata_payload or {})
    metadata["last_indexed_at"] = (datetime.now(UTC) - timedelta(days=8)).isoformat()
    document.metadata_payload = metadata
    await db_session.commit()

    second = await ingest_knowledge_file_to_vertex(
        db_session,
        file_path=str(source_file),
        source_uri="mekong-salt://tests/thresholds",
        source_key="thresholds-tests",
        effective_date="2026-04-01",
        document_type="threshold",
        tags=["threshold", "csv"],
    )

    assert second.version == 2
    assert second.reindexed is True
    assert second.skipped is False
    assert calls["remove"] == 1
    assert calls["upsert"] == 2

    refreshed = await repo.get_by_source_uri("mekong-salt://tests/thresholds")
    assert refreshed is not None
    refreshed_metadata = dict(refreshed.metadata_payload or {})
    assert refreshed_metadata.get("source_key") == "thresholds-tests"
    assert refreshed_metadata.get("effective_date") == "2026-04-01"
    assert refreshed_metadata.get("document_version") == 2
    assert refreshed_metadata.get("version_history")


@pytest.mark.asyncio
async def test_ingestion_marks_registry_failed_and_increments_retry_on_provider_error(
    db_session,
    monkeypatch,
    tmp_path: Path,
):
    class BrokenVectorService:
        async def embed_texts(self, texts: list[str]) -> list[list[float]]:
            return [[0.01] * 768 for _ in texts]

        async def upsert_datapoints(self, datapoints):
            raise RuntimeError("simulated provider write failure")

        async def remove_datapoints(self, datapoint_ids):
            return None

    class FakeSettings:
        rag_csv_reindex_ttl_days = 1

    monkeypatch.setattr(
        "app.services.rag.ingestion_service.VertexVectorSearchService",
        lambda: BrokenVectorService(),
    )
    monkeypatch.setattr(
        "app.services.rag.ingestion_service.get_settings",
        lambda: FakeSettings(),
    )

    source_file = tmp_path / "broken-sync.csv"
    source_file.write_text(
        "policy_id,warning_threshold_dsm,critical_threshold_dsm\n"
        "POL-ERR,2.6,4.1\n",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="simulated provider write failure"):
        await ingest_knowledge_file_to_vertex(
            db_session,
            file_path=str(source_file),
            source_uri="mekong-salt://tests/broken-sync",
            source_key="broken-sync-tests",
            effective_date="2026-04-01",
            document_type="threshold",
            tags=["threshold", "csv"],
        )

    repo = KnowledgeDocumentRepository(db_session)
    document = await repo.get_by_source_uri("mekong-salt://tests/broken-sync")
    assert document is not None
    assert document.provider_sync_status == "failed"
    assert document.provider_retry_count == 1
    assert document.provider_last_retry_at is not None
    assert document.provider_error is not None


@pytest.mark.asyncio
async def test_ingestion_strips_null_bytes_from_content_before_persist(
    db_session,
    monkeypatch,
    tmp_path: Path,
):
    class FakeVectorService:
        async def embed_texts(self, texts: list[str]) -> list[list[float]]:
            return [[0.01] * 768 for _ in texts]

        async def upsert_datapoints(self, datapoints):
            return None

        async def remove_datapoints(self, datapoint_ids):
            return None

    class FakeSettings:
        rag_csv_reindex_ttl_days = 1

    monkeypatch.setattr(
        "app.services.rag.ingestion_service.VertexVectorSearchService",
        lambda: FakeVectorService(),
    )
    monkeypatch.setattr(
        "app.services.rag.ingestion_service.get_settings",
        lambda: FakeSettings(),
    )

    source_file = tmp_path / "null-byte-threshold.txt"
    source_file.write_text("line1\x00line2\nline3\x00", encoding="utf-8")

    await ingest_knowledge_file_to_vertex(
        db_session,
        file_path=str(source_file),
        source_uri="mekong-salt://tests/null-byte-threshold",
        source_key="null-byte-threshold-tests",
        effective_date="2026-04-01",
        document_type="threshold",
        tags=["threshold", "txt"],
    )

    repo = KnowledgeDocumentRepository(db_session)
    document = await repo.get_by_source_uri("mekong-salt://tests/null-byte-threshold")
    assert document is not None
    assert "\x00" not in (document.content_text or "")
    assert "\x00" not in (document.summary or "")


@pytest.mark.asyncio
async def test_ingestion_reindexes_when_existing_document_has_no_chunks_and_failed_sync(
    db_session,
    monkeypatch,
    tmp_path: Path,
):
    calls = {"upsert": 0}

    class FakeVectorService:
        async def embed_texts(self, texts: list[str]) -> list[list[float]]:
            return [[0.01] * 768 for _ in texts]

        async def upsert_datapoints(self, datapoints):
            calls["upsert"] += 1

        async def remove_datapoints(self, datapoint_ids):
            return None

    class FakeSettings:
        rag_csv_reindex_ttl_days = 7

    monkeypatch.setattr(
        "app.services.rag.ingestion_service.VertexVectorSearchService",
        lambda: FakeVectorService(),
    )
    monkeypatch.setattr(
        "app.services.rag.ingestion_service.get_settings",
        lambda: FakeSettings(),
    )

    source_uri = "mekong-salt://tests/reindex-failed-no-chunks"
    source_file = tmp_path / "reindex-failed-no-chunks.txt"
    source_text = "threshold policy baseline"
    source_file.write_text(source_text, encoding="utf-8")
    source_hash = hashlib.sha256(source_text.encode("utf-8")).hexdigest()

    existing = KnowledgeDocument(
        title="Legacy Failed Doc",
        source_uri=source_uri,
        document_type="threshold",
        summary="legacy",
        content_text="threshold policy baseline",
        tags=["threshold"],
        metadata_payload={
            "content_sha256": source_hash,
            "document_version": 1,
            "effective_date": "2026-04-01",
            "last_indexed_at": datetime.now(UTC).isoformat(),
            "version_history": [],
        },
        source_key="reindex-failed-no-chunks",
        content_sha256=source_hash,
        document_version=1,
        provider_sync_status="failed",
        provider_retry_count=1,
    )
    db_session.add(existing)
    await db_session.commit()

    result = await ingest_knowledge_file_to_vertex(
        db_session,
        file_path=str(source_file),
        source_uri=source_uri,
        source_key="reindex-failed-no-chunks",
        effective_date="2026-04-01",
        document_type="threshold",
        tags=["threshold", "txt"],
    )

    assert result.reindexed is True
    assert result.skipped is False
    assert calls["upsert"] == 1
