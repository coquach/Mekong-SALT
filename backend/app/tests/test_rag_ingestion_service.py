"""Tests for governance behavior in RAG ingestion service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

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
    }

    class FakeVectorService:
        async def embed_texts(self, texts: list[str]) -> list[list[float]]:
            return [[0.01] * 768 for _ in texts]

        async def upsert_datapoints(self, datapoints):
            calls["upsert"] += 1

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
