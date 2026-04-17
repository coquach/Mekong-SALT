"""Tests for static retrieval lane provider selection and shadow gates."""

from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.services.rag.retrieval_policy import RetrievalLanePolicy
from app.services.rag.static_document_lane import retrieve_static_document_lane


@pytest.mark.asyncio
async def test_static_lane_shadow_mode_selects_local_when_overlap_below_threshold(
    db_session,
    monkeypatch,
):
    class FakeNeighbor:
        def __init__(self, datapoint_id: str, distance: float) -> None:
            self.datapoint_id = datapoint_id
            self.distance = distance

    class FakeVectorService:
        def is_configured(self) -> bool:
            return True

        async def embed_texts(self, texts):
            return [[0.2, 0.4, 0.6]]

        async def find_neighbors(self, *, query_embedding, neighbor_count, restricts=None):
            return [FakeNeighbor(str(uuid4()), 0.2)]

    async def fake_local_candidates(self, *, category, query_terms, limit):
        doc = SimpleNamespace(
            id=uuid4(),
            title="Local SOP",
            summary="fallback",
            document_type="sop",
            source_uri="mekong-salt://local/sop",
            tags=["sop"],
            metadata_payload={"region_code": "global"},
        )
        chunk = SimpleNamespace(id=uuid4(), content_text="local fallback evidence")
        return [(chunk, doc)]

    monkeypatch.setattr(
        "app.repositories.knowledge.KnowledgeDocumentRepository.list_ranked_chunk_candidates",
        fake_local_candidates,
    )

    policy = RetrievalLanePolicy(
        use_vector_search=True,
        enable_local_fallback=True,
        static_corpus_provider="vector_search",
        static_retrieval_mode="shadow",
        shadow_primary_lane="vector",
        shadow_min_overlap_ratio=0.9,
        top_k=8,
        static_local_limit=1,
        memory_local_limit=1,
        memory_vector_max_evidence=1,
        memory_vector_timeout_seconds=1.0,
        vector_neighbor_multiplier=2,
        vector_neighbor_floor=12,
    )

    assessment = SimpleNamespace(
        risk_level=SimpleNamespace(value="warning"),
        summary="warning salinity",
        trend_direction=SimpleNamespace(value="rising"),
    )

    evidence, vector_used, fallback_used = await retrieve_static_document_lane(
        db_session,
        policy=policy,
        objective="Protect intake",
        assessment=assessment,
        query_terms=["warning", "sop"],
        max_evidence=4,
        vector_service_factory=lambda: FakeVectorService(),
    )

    assert vector_used is False
    assert fallback_used is True
    assert evidence
    assert evidence[0]["metadata"]["shadow_mode"]["selected_lane"] == "local"
