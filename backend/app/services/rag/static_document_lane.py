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

    if policy.use_vector_search:
        try:
            evidence.extend(
                await _retrieve_document_evidence_from_vector(
                    session,
                    objective=objective,
                    assessment=assessment,
                    query_terms=query_terms,
                    max_evidence=max_evidence,
                    top_k=policy.top_k,
                    neighbor_multiplier=policy.vector_neighbor_multiplier,
                    neighbor_floor=policy.vector_neighbor_floor,
                    vector_service_factory=vector_service_factory,
                )
            )
            vector_used = bool(evidence)
        except Exception:
            if not policy.enable_local_fallback:
                raise

    if not evidence and policy.enable_local_fallback:
        fallback_used = True
        sop_rows = await document_repo.list_ranked_chunk_candidates(
            category="sop",
            query_terms=query_terms,
            limit=policy.static_local_limit,
        )
        threshold_rows = await document_repo.list_ranked_chunk_candidates(
            category="threshold",
            query_terms=query_terms,
            limit=policy.static_local_limit,
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
) -> list[dict[str, Any]]:
    """Retrieve document chunks via vector search and map them to evidence rows."""
    vector_service = vector_service_factory()
    static_provider = get_static_corpus_provider(vector_service=vector_service)
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
