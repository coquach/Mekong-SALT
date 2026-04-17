"""Retrieval broker for composing static and dynamic evidence lanes."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy.exc import SQLAlchemyError


@dataclass(slots=True)
class RetrievalBrokerResult:
    """Composed retrieval output before contract serialization."""

    evidence: list[dict[str, Any]]
    vector_search_used: bool
    local_fallback_used: bool
    total_candidates: int


async def collect_ranked_evidence(
    *,
    max_evidence: int,
    static_lane_loader: Callable[[], Awaitable[tuple[list[dict[str, Any]], bool, bool]]],
    similar_case_lane_loader: Callable[[], Awaitable[list[dict[str, Any]]]],
    memory_case_lane_loader: Callable[[], Awaitable[tuple[list[dict[str, Any]], bool, bool]]],
) -> RetrievalBrokerResult:
    """Collect evidence from lanes and apply late-fusion ranking."""
    evidence: list[dict[str, Any]] = []

    static_evidence, vector_search_used, local_fallback_used = await static_lane_loader()
    evidence.extend(static_evidence)
    evidence.extend(await similar_case_lane_loader())

    try:
        memory_case_evidence, memory_vector_used, memory_fallback_used = await memory_case_lane_loader()
        evidence.extend(memory_case_evidence)
        vector_search_used = vector_search_used or memory_vector_used
        local_fallback_used = local_fallback_used or memory_fallback_used
    except SQLAlchemyError:
        # Support environments where memory_cases migration has not been applied yet.
        pass

    deduped = _dedupe_evidence(evidence)
    ranked = sorted(deduped, key=lambda item: item["score"], reverse=True)[:max_evidence]
    for rank, item in enumerate(ranked, start=1):
        item["rank"] = rank

    return RetrievalBrokerResult(
        evidence=ranked,
        vector_search_used=vector_search_used,
        local_fallback_used=local_fallback_used,
        total_candidates=len(evidence),
    )


def _dedupe_evidence(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, Any]] = []
    for item in items:
        if item["evidence_type"] == "knowledge_document":
            key = ("knowledge", f"{item.get('document_id')}::{item.get('chunk_id')}")
        elif item["evidence_type"] == "memory_case":
            key = ("memory_case", str(item.get("memory_case_id")))
        else:
            key = ("case", str(item.get("incident_id")))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped
