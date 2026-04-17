"""Planning-time retrieval service for grounded context enrichment."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from app.core.config import get_settings
from app.schemas.retrieval import (
    RetrievalContext,
    RetrievalPolicyFlags,
    RetrievalProvenance,
    RetrievalRankingMetadata,
)
from app.services.rag.retrieval_broker import collect_ranked_evidence
from app.services.rag.memory_case_lane import retrieve_memory_case_lane
from app.services.rag.similar_case_lane import retrieve_similar_case_lane
from app.services.rag.static_document_lane import retrieve_static_document_lane
from app.services.rag.vertex_vector_search_service import VertexVectorSearchService

_DEFAULT_MAX_EVIDENCE = 8
_STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "into",
    "water",
    "salinity",
    "risk",
    "reduce",
    "protect",
    "plan",
    "mvp",
}


async def retrieve_ranked_knowledge_context(
    session,
    *,
    objective: str,
    risk_bundle,
    max_evidence: int = _DEFAULT_MAX_EVIDENCE,
) -> RetrievalContext:
    """Build ranked RAG evidence from SOP docs, threshold docs, and similar cases."""
    settings = get_settings()
    rag_top_k = int(getattr(settings, "rag_retrieval_top_k", 8))
    assessment = risk_bundle.assessment
    risk_level = assessment.risk_level.value
    query_terms = _extract_query_terms(
        " ".join(
            filter(
                None,
                [
                    objective,
                    getattr(assessment, "summary", None),
                    risk_level,
                    getattr(getattr(assessment, "trend_direction", None), "value", None),
                ],
            )
        )
    )

    broker_result = await collect_ranked_evidence(
        max_evidence=max_evidence,
        static_lane_loader=lambda: retrieve_static_document_lane(
            session,
            settings=settings,
            objective=objective,
            assessment=assessment,
            query_terms=query_terms,
            max_evidence=max_evidence,
            top_k=rag_top_k,
            vector_service_factory=VertexVectorSearchService,
        ),
        similar_case_lane_loader=lambda: retrieve_similar_case_lane(
            session,
            assessment=assessment,
            query_terms=query_terms,
            risk_level=risk_level,
        ),
        memory_case_lane_loader=lambda: retrieve_memory_case_lane(
            session,
            settings=settings,
            objective=objective,
            assessment=assessment,
            query_terms=query_terms,
            risk_level=risk_level,
            top_k=rag_top_k,
            vector_service_factory=VertexVectorSearchService,
        ),
    )

    source_counts = _build_source_counts(broker_result.evidence)
    ranking_metadata = RetrievalRankingMetadata(
        max_evidence=max(max_evidence, 1),
        top_k=max(rag_top_k, 1),
        query_terms=query_terms,
        top_citations=_build_top_citations(broker_result.evidence),
    )
    provenance = RetrievalProvenance(
        generated_at=datetime.now(UTC),
        vector_search_enabled=bool(settings.rag_use_vertex_vector_search),
        vector_search_used=broker_result.vector_search_used,
        local_fallback_enabled=bool(settings.rag_enable_local_fallback),
        local_fallback_used=broker_result.local_fallback_used,
        source_counts=source_counts,
        total_candidates=broker_result.total_candidates,
    )
    policy_flags = RetrievalPolicyFlags(
        simulation_only=True,
        requires_human_approval=True,
        allow_hardware_execution=False,
        evidence_minimum_required=1,
        deterministic_ranking=True,
    )

    return RetrievalContext.model_validate(
        {
            "evidence": broker_result.evidence,
            "provenance": provenance.model_dump(mode="json"),
            "ranking_metadata": ranking_metadata.model_dump(mode="json"),
            "policy_flags": policy_flags.model_dump(mode="json"),
        }
    )


def _extract_query_terms(raw: str) -> list[str]:
    terms = []
    for token in re.findall(r"[a-zA-Z0-9_-]+", raw.lower()):
        if len(token) < 3:
            continue
        if token in _STOP_WORDS:
            continue
        if token not in terms:
            terms.append(token)
    return terms[:16]


def _build_source_counts(knowledge_context: list[dict[str, Any]]) -> dict[str, int]:
    source_counts: dict[str, int] = {}
    for item in knowledge_context:
        source = str(item.get("evidence_source") or "unknown")
        source_counts[source] = source_counts.get(source, 0) + 1
    return source_counts


def _build_top_citations(knowledge_context: list[dict[str, Any]]) -> list[dict[str, Any]]:
    top_citations: list[dict[str, Any]] = []
    for item in knowledge_context[:5]:
        top_citations.append(
            {
                "rank": item.get("rank"),
                "score": item.get("score"),
                "evidence_source": item.get("evidence_source"),
                "citation": item.get("citation"),
            }
        )
    return top_citations
