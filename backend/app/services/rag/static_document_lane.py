"""Static institutional knowledge retrieval lane."""

from __future__ import annotations

from typing import Any, Callable
from uuid import UUID

from app.repositories.knowledge import KnowledgeDocumentRepository
from app.services.rag.retrieval_policy import RetrievalLanePolicy
from app.services.rag.retrieval_builders import (
    build_document_evidence,
    infer_doc_source,
    score_bias_from_distance,
)
from app.services.rag.static_corpus_provider import get_static_corpus_provider


async def retrieve_static_document_lane(
    session,
    *,
    policy: RetrievalLanePolicy,
    objective: str,
    assessment,
    query_terms: list[str],
    max_evidence: int,
    vector_service_factory: Callable[[], Any],
) -> tuple[list[dict[str, Any]], bool, bool]:
    """Retrieve static institutional knowledge through provider then local fallback."""
    risk_level = getattr(getattr(assessment, "risk_level", None), "value", "")
    document_repo = KnowledgeDocumentRepository(session)

    evidence: list[dict[str, Any]] = []
    vector_used = False
    fallback_used = False

    mode = str(policy.static_retrieval_mode or "vector").lower()
    local_evidence = await _retrieve_document_evidence_from_local(
        document_repo,
        query_terms=query_terms,
        risk_level=risk_level,
        local_limit=policy.static_local_limit,
    )

    vector_evidence: list[dict[str, Any]] = []
    if policy.use_vector_search and mode in {"vector", "shadow"}:
        try:
            vector_evidence = await _retrieve_document_evidence_from_vector(
                session,
                objective=objective,
                assessment=assessment,
                query_terms=query_terms,
                max_evidence=max_evidence,
                top_k=policy.top_k,
                neighbor_multiplier=policy.vector_neighbor_multiplier,
                neighbor_floor=policy.vector_neighbor_floor,
                vector_service_factory=vector_service_factory,
                static_provider_name=policy.static_corpus_provider,
            )
            vector_used = bool(vector_evidence)
        except Exception:
            if not policy.enable_local_fallback and mode != "shadow":
                raise

    if mode == "local":
        evidence.extend(local_evidence)
        fallback_used = bool(local_evidence)
    elif mode == "shadow":
        selected_lane = _select_shadow_lane(
            vector_evidence=vector_evidence,
            local_evidence=local_evidence,
            primary_lane=policy.shadow_primary_lane,
            min_overlap_ratio=policy.shadow_min_overlap_ratio,
        )
        evidence.extend(vector_evidence if selected_lane == "vector" else local_evidence)
        fallback_used = selected_lane == "local" and bool(local_evidence)
        _annotate_shadow_selection(
            evidence,
            selected_lane=selected_lane,
            vector_count=len(vector_evidence),
            local_count=len(local_evidence),
            overlap_ratio=_compute_overlap_ratio(vector_evidence, local_evidence),
        )
    else:
        evidence.extend(vector_evidence)
        if not evidence and policy.enable_local_fallback:
            evidence.extend(local_evidence)
            fallback_used = bool(local_evidence)

    return evidence, vector_used, fallback_used


async def _retrieve_document_evidence_from_vector(
    session,
    *,
    objective: str,
    assessment,
    query_terms: list[str],
    max_evidence: int,
    top_k: int,
    neighbor_multiplier: int,
    neighbor_floor: int,
    vector_service_factory: Callable[[], Any],
    static_provider_name: str,
) -> list[dict[str, Any]]:
    """Retrieve document chunks via vector search and map them to evidence rows."""
    vector_service = vector_service_factory()
    static_provider = get_static_corpus_provider(
        settings=type("SettingsAdapter", (), {"rag_static_corpus_provider": static_provider_name})(),
        vector_service=vector_service,
    )
    if not static_provider.is_configured():
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

    vectors = await static_provider.embed_texts([query_text])
    if not vectors:
        return []

    neighbors = await static_provider.find_neighbors(
        query_embedding=vectors[0],
        neighbor_count=max(max(top_k, max_evidence) * max(1, neighbor_multiplier), max(1, neighbor_floor)),
        restricts={"entity_type": ["knowledge_document"]},
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

    rows = await KnowledgeDocumentRepository(session).list_chunks_with_documents_by_ids(parsed_ids)
    by_chunk_id = {str(chunk.id): (chunk, document) for chunk, document in rows}

    evidence: list[dict[str, Any]] = []
    risk_level = getattr(getattr(assessment, "risk_level", None), "value", "")
    for neighbor in neighbors:
        key = neighbor.datapoint_id
        if key not in by_chunk_id:
            continue
        chunk, document = by_chunk_id[key]
        source = infer_doc_source(document)
        evidence.append(
            build_document_evidence(
                document=document,
                chunk=chunk,
                source=source,
                risk_level=risk_level,
                query_terms=query_terms,
                score_bias=score_bias_from_distance(neighbor.distance),
            )
        )

    distance_order = {chunk_id: index for index, chunk_id in enumerate(ordered_ids)}
    evidence.sort(
        key=lambda item: (
            -item["score"],
            distance_order.get(item.get("chunk_id", ""), 9999),
        )
    )
    return evidence[:max(max_evidence, 1)]


async def _retrieve_document_evidence_from_local(
    document_repo: KnowledgeDocumentRepository,
    *,
    query_terms: list[str],
    risk_level: str,
    local_limit: int,
) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    sop_rows = await document_repo.list_ranked_chunk_candidates(
        category="sop",
        query_terms=query_terms,
        limit=local_limit,
    )
    threshold_rows = await document_repo.list_ranked_chunk_candidates(
        category="threshold",
        query_terms=query_terms,
        limit=local_limit,
    )

    for chunk, document in sop_rows:
        evidence.append(
            build_document_evidence(
                document=document,
                chunk=chunk,
                source="sop_doc",
                risk_level=risk_level,
                query_terms=query_terms,
                score_bias=2.2,
            )
        )
    for chunk, document in threshold_rows:
        evidence.append(
            build_document_evidence(
                document=document,
                chunk=chunk,
                source="threshold_doc",
                risk_level=risk_level,
                query_terms=query_terms,
                score_bias=2.0,
            )
        )
    return evidence


def _citation_key(item: dict[str, Any]) -> tuple[str, str]:
    return (
        str(item.get("document_id") or ""),
        str(item.get("chunk_id") or ""),
    )


def _compute_overlap_ratio(vector_evidence: list[dict[str, Any]], local_evidence: list[dict[str, Any]]) -> float:
    if not vector_evidence or not local_evidence:
        return 0.0
    vector_keys = {_citation_key(item) for item in vector_evidence}
    local_keys = {_citation_key(item) for item in local_evidence}
    overlap = len(vector_keys.intersection(local_keys))
    base = max(1, min(len(vector_keys), len(local_keys)))
    return overlap / base


def _select_shadow_lane(
    *,
    vector_evidence: list[dict[str, Any]],
    local_evidence: list[dict[str, Any]],
    primary_lane: str,
    min_overlap_ratio: float,
) -> str:
    preferred = "vector" if str(primary_lane).lower() != "local" else "local"
    if preferred == "vector":
        if not vector_evidence:
            return "local"
        if not local_evidence:
            return "vector"
        overlap_ratio = _compute_overlap_ratio(vector_evidence, local_evidence)
        return "vector" if overlap_ratio >= min_overlap_ratio else "local"

    if local_evidence:
        return "local"
    return "vector"


def _annotate_shadow_selection(
    evidence: list[dict[str, Any]],
    *,
    selected_lane: str,
    vector_count: int,
    local_count: int,
    overlap_ratio: float,
) -> None:
    for item in evidence:
        metadata = dict(item.get("metadata") or {})
        metadata["shadow_mode"] = {
            "selected_lane": selected_lane,
            "vector_count": vector_count,
            "local_count": local_count,
            "overlap_ratio": round(overlap_ratio, 3),
        }
        item["metadata"] = metadata
