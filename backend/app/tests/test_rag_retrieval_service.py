"""Tests for Vertex-first RAG retrieval behavior."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.models.knowledge import EmbeddedChunk, KnowledgeDocument
from app.models.enums import RiskLevel, TrendDirection
from app.services.rag.retrieval_service import retrieve_ranked_knowledge_context


@pytest.mark.asyncio
async def test_retrieve_ranked_knowledge_context_uses_vertex_neighbors(
    db_session,
    monkeypatch,
):
    doc_sop = KnowledgeDocument(
        title="Operations SOP for salinity",
        source_uri=f"mekong-salt://vertex/sop-{uuid4().hex}",
        document_type="guideline",
        summary="SOP recommendations.",
        content_text="Send alerts and simulate gate operations.",
        tags=["sop", "operations"],
        metadata_payload={"source": "test"},
    )
    doc_threshold = KnowledgeDocument(
        title="Critical salinity threshold policy",
        source_uri=f"mekong-salt://vertex/threshold-{uuid4().hex}",
        document_type="threshold",
        summary="Threshold guidance.",
        content_text="Warning is 2.5 dS/m and critical is 4.0 dS/m.",
        tags=["threshold", "critical"],
        metadata_payload={"source": "test"},
    )
    db_session.add_all([doc_sop, doc_threshold])
    await db_session.flush()

    chunk_sop = EmbeddedChunk(
        document_id=doc_sop.id,
        chunk_index=0,
        content_text=doc_sop.content_text,
        token_count=10,
        embedding=[0.01] * 768,
        metadata_payload={"section": "ops"},
    )
    chunk_threshold = EmbeddedChunk(
        document_id=doc_threshold.id,
        chunk_index=0,
        content_text=doc_threshold.content_text,
        token_count=12,
        embedding=[0.02] * 768,
        metadata_payload={"section": "threshold"},
    )
    db_session.add_all([chunk_sop, chunk_threshold])
    await db_session.commit()

    class FakeNeighbor:
        def __init__(self, datapoint_id: str, distance: float) -> None:
            self.datapoint_id = datapoint_id
            self.distance = distance

    class FakeVertexService:
        def is_configured(self) -> bool:
            return True

        async def embed_texts(self, texts: list[str]) -> list[list[float]]:
            assert texts
            return [[0.5, 0.25, 0.75]]

        async def find_neighbors(self, *, query_embedding, neighbor_count):
            assert query_embedding
            assert neighbor_count >= 2
            return [
                FakeNeighbor(str(chunk_sop.id), 0.12),
                FakeNeighbor(str(chunk_threshold.id), 0.18),
            ]

    monkeypatch.setattr(
        "app.services.rag.retrieval_service.VertexVectorSearchService",
        lambda: FakeVertexService(),
    )

    class FakeSettings:
        rag_use_vertex_vector_search = True
        rag_enable_local_fallback = True

    monkeypatch.setattr(
        "app.services.rag.retrieval_service.get_settings",
        lambda: FakeSettings(),
    )

    risk_bundle = SimpleNamespace(
        assessment=SimpleNamespace(
            id=uuid4(),
            region_id=uuid4(),
            risk_level=RiskLevel.WARNING,
            trend_direction=TrendDirection.RISING,
            trend_delta_dsm=Decimal("0.20"),
            summary="Warning salinity spike.",
            rationale={"source": "test"},
        ),
        reading=SimpleNamespace(),
        weather_snapshot=None,
    )

    context = await retrieve_ranked_knowledge_context(
        db_session,
        objective="Use SOP and threshold evidence",
        risk_bundle=risk_bundle,
        max_evidence=6,
    )

    evidence = context.evidence
    assert evidence
    assert any(item.evidence_source == "sop_doc" for item in evidence)
    assert any(item.evidence_source == "threshold_doc" for item in evidence)
    assert all(item.snippet for item in evidence)
    assert all(item.citation for item in evidence)
    assert all(item.metadata_filters for item in evidence)
    assert evidence[0].score >= evidence[-1].score


@pytest.mark.asyncio
async def test_retrieve_ranked_knowledge_context_includes_memory_case_evidence(
    db_session,
    monkeypatch,
):
    region_id = uuid4()

    class FakeMemoryCase:
        def __init__(self) -> None:
            self.id = uuid4()
            self.region_id = region_id
            self.station_id = None
            self.incident_id = None
            self.action_plan_id = None
            self.action_execution_id = None
            self.severity = RiskLevel.WARNING.value
            self.objective = "Protect irrigation intake"
            self.outcome_class = "success"
            self.outcome_status_legacy = "improved"
            self.summary = "Previous warning-level case improved after advisory + wait-safe-window."
            self.keywords = ["warning", "wait-safe-window", "irrigation"]
            self.occurred_at = datetime.now(UTC)

    async def fake_list_similar_cases(self, *, region_id, severity, query_terms, limit):
        return [FakeMemoryCase()]

    async def fake_is_table_ready(self):
        return True

    monkeypatch.setattr(
        "app.repositories.memory_case.MemoryCaseRepository.list_similar_cases",
        fake_list_similar_cases,
    )
    monkeypatch.setattr(
        "app.repositories.memory_case.MemoryCaseRepository.is_table_ready",
        fake_is_table_ready,
    )

    class FakeVertexService:
        def is_configured(self) -> bool:
            return False

    monkeypatch.setattr(
        "app.services.rag.retrieval_service.VertexVectorSearchService",
        lambda: FakeVertexService(),
    )

    class FakeSettings:
        rag_use_vertex_vector_search = True
        rag_enable_local_fallback = False
        rag_retrieval_top_k = 8

    monkeypatch.setattr(
        "app.services.rag.retrieval_service.get_settings",
        lambda: FakeSettings(),
    )

    risk_bundle = SimpleNamespace(
        assessment=SimpleNamespace(
            id=uuid4(),
            region_id=region_id,
            risk_level=RiskLevel.WARNING,
            trend_direction=TrendDirection.RISING,
            trend_delta_dsm=Decimal("0.15"),
            summary="Warning salinity drift.",
            rationale={"source": "test"},
        ),
        reading=SimpleNamespace(),
        weather_snapshot=None,
    )

    context = await retrieve_ranked_knowledge_context(
        db_session,
        objective="Reuse successful warning-case actions",
        risk_bundle=risk_bundle,
        max_evidence=6,
    )

    evidence = context.evidence
    assert any(item.evidence_source == "memory_case" for item in evidence)
