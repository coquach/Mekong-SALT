"""Episodic memory-case retrieval lane."""

from __future__ import annotations

import asyncio
from typing import Any, Callable
from uuid import UUID

from app.repositories.memory_case import MemoryCaseRepository
from app.services.rag.retrieval_builders import build_memory_case_evidence, score_bias_from_distance


async def retrieve_memory_case_lane(
    session,
    *,
    settings,
    objective: str,
    assessment,
    query_terms: list[str],
    risk_level: str,
    top_k: int,
    vector_service_factory: Callable[[], Any],
) -> tuple[list[dict[str, Any]], bool, bool]:
    """Retrieve episodic memory evidence (vector first, DB fallback)."""
    memory_case_repo = MemoryCaseRepository(session)
    if not await memory_case_repo.is_table_ready():
        return [], False, False

    vector_used = False
    fallback_used = False
    memory_case_evidence: list[dict[str, Any]] = []
    if settings.rag_use_vertex_vector_search:
        try:
            memory_case_evidence = await asyncio.wait_for(
                _retrieve_memory_case_evidence_from_vector(
                    session,
                    objective=objective,
                    assessment=assessment,
                    query_terms=query_terms,
                    max_evidence=4,
                    top_k=top_k,
                    vector_service_factory=vector_service_factory,
                ),
                timeout=2.5,
            )
            vector_used = bool(memory_case_evidence)
        except Exception:
            memory_case_evidence = []

    if not memory_case_evidence:
        memory_cases = await memory_case_repo.list_similar_cases(
            region_id=assessment.region_id,
            severity=risk_level,
            query_terms=query_terms,
            limit=4,
        )
        fallback_used = bool(memory_cases)
        for case in memory_cases:
            memory_case_evidence.append(
                build_memory_case_evidence(
                    memory_case=case,
                    query_terms=query_terms,
                    risk_level=risk_level,
                )
            )

    return memory_case_evidence, vector_used, fallback_used


async def _retrieve_memory_case_evidence_from_vector(
    session,
    *,
    objective: str,
    assessment,
    query_terms: list[str],
    max_evidence: int,
    top_k: int,
    vector_service_factory: Callable[[], Any],
) -> list[dict[str, Any]]:
    """Retrieve memory-case evidence via vector search and hydrate from DB rows."""
    vector_service = vector_service_factory()
    if not vector_service.is_configured():
        return []

    query_text = " ".join(
        filter(
            None,
            [
                objective,
                getattr(assessment, "summary", None),
                getattr(getattr(assessment, "risk_level", None), "value", None),
                getattr(getattr(assessment, "trend_direction", None), "value", None),
            ],
        )
    )

    vectors = await vector_service.embed_texts([query_text])
    if not vectors:
        return []

    neighbors = await vector_service.find_neighbors(
        query_embedding=vectors[0],
        neighbor_count=max(max(top_k, max_evidence) * 2, 12),
        restricts={
            "entity_type": ["memory_case"],
            "region_scope": [str(getattr(assessment, "region_id"))],
        },
    )
    if not neighbors:
        return []

    parsed_ids: list[UUID] = []
    ordered_ids: list[str] = []
    for neighbor in neighbors:
        try:
            parsed_ids.append(UUID(neighbor.datapoint_id))
            ordered_ids.append(neighbor.datapoint_id)
        except ValueError:
            continue
    if not parsed_ids:
        return []

    cases = await MemoryCaseRepository(session).list_by_ids(parsed_ids)
    case_by_id = {str(case.id): case for case in cases}

    evidence: list[dict[str, Any]] = []
    risk_level = getattr(getattr(assessment, "risk_level", None), "value", "")
    for neighbor in neighbors:
        case = case_by_id.get(neighbor.datapoint_id)
        if case is None:
            continue
        item = build_memory_case_evidence(
            memory_case=case,
            query_terms=query_terms,
            risk_level=risk_level,
        )
        item["score"] = round(item["score"] + score_bias_from_distance(neighbor.distance), 3)
        evidence.append(item)

    distance_order = {case_id: index for index, case_id in enumerate(ordered_ids)}
    evidence.sort(
        key=lambda item: (
            -item["score"],
            distance_order.get(item.get("memory_case_id", ""), 9999),
        )
    )
    return evidence[:max(max_evidence, 1)]
