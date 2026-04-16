"""Planning-time retrieval service for grounded context enrichment."""

from __future__ import annotations

import asyncio
import re
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.models.enums import IncidentStatus
from app.repositories.action import ActionPlanRepository
from app.repositories.knowledge import KnowledgeDocumentRepository, SimilarCaseRepository
from app.repositories.memory_case import MemoryCaseRepository
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
) -> list[dict[str, Any]]:
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

    document_repo = KnowledgeDocumentRepository(session)
    case_repo = SimilarCaseRepository(session)
    memory_case_repo = MemoryCaseRepository(session)
    action_repo = ActionPlanRepository(session)

    evidence: list[dict[str, Any]] = []
    if settings.rag_use_vertex_vector_search:
        try:
            evidence.extend(
                await _retrieve_document_evidence_from_vertex(
                    session,
                    objective=objective,
                    assessment=assessment,
                    query_terms=query_terms,
                    max_evidence=max_evidence,
                    top_k=rag_top_k,
                )
            )
        except Exception:
            if not settings.rag_enable_local_fallback:
                raise

    if not evidence and settings.rag_enable_local_fallback:
        sop_rows = await document_repo.list_ranked_chunk_candidates(
            category="sop",
            query_terms=query_terms,
            limit=4,
        )
        threshold_rows = await document_repo.list_ranked_chunk_candidates(
            category="threshold",
            query_terms=query_terms,
            limit=4,
        )

        for chunk, document in sop_rows:
            evidence.append(
                _build_document_evidence(
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
                _build_document_evidence(
                    document=document,
                    chunk=chunk,
                    source="threshold_doc",
                    risk_level=risk_level,
                    query_terms=query_terms,
                    score_bias=2.0,
                )
            )

    similar_incidents = await case_repo.list_similar_incidents(
        region_id=assessment.region_id,
        severity=assessment.risk_level,
        exclude_assessment_id=getattr(assessment, "id", None),
        limit=4,
    )
    for incident in similar_incidents:
        latest_plan = await action_repo.get_latest_for_incident(incident.id)
        evidence.append(
            _build_case_evidence(
                incident=incident,
                latest_plan=latest_plan,
                query_terms=query_terms,
                risk_level=risk_level,
            )
        )

    try:
        if await memory_case_repo.is_table_ready():
            memory_case_evidence: list[dict[str, Any]] = []
            if settings.rag_use_vertex_vector_search:
                try:
                    memory_case_evidence = await asyncio.wait_for(
                        _retrieve_memory_case_evidence_from_vertex(
                            session,
                            objective=objective,
                            assessment=assessment,
                            query_terms=query_terms,
                            max_evidence=4,
                            top_k=rag_top_k,
                        ),
                        timeout=2.5,
                    )
                except Exception:
                    # Memory-case semantic lookup is best-effort and should not block planning.
                    memory_case_evidence = []

            if not memory_case_evidence:
                memory_cases = await memory_case_repo.list_similar_cases(
                    region_id=assessment.region_id,
                    severity=risk_level,
                    query_terms=query_terms,
                    limit=4,
                )
                for case in memory_cases:
                    memory_case_evidence.append(
                        _build_memory_case_evidence(
                            memory_case=case,
                            query_terms=query_terms,
                            risk_level=risk_level,
                        )
                    )

            evidence.extend(memory_case_evidence)
    except SQLAlchemyError:
        # Support environments where memory_cases migration has not been applied yet.
        pass

    deduped = _dedupe_evidence(evidence)
    ranked = sorted(deduped, key=lambda item: item["score"], reverse=True)[:max_evidence]
    for rank, item in enumerate(ranked, start=1):
        item["rank"] = rank
    return ranked


async def _retrieve_document_evidence_from_vertex(
    session,
    *,
    objective: str,
    assessment,
    query_terms: list[str],
    max_evidence: int,
    top_k: int,
) -> list[dict[str, Any]]:
    """Retrieve document chunks via Vertex Vector Search and map them to evidence rows."""
    vector_service = VertexVectorSearchService()
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
        source = _infer_doc_source(document)
        evidence.append(
            _build_document_evidence(
                document=document,
                chunk=chunk,
                source=source,
                risk_level=risk_level,
                query_terms=query_terms,
                score_bias=_score_bias_from_distance(neighbor.distance),
            )
        )

    # Preserve nearest-neighbor priority when scores tie.
    distance_order = {chunk_id: index for index, chunk_id in enumerate(ordered_ids)}
    evidence.sort(
        key=lambda item: (
            -item["score"],
            distance_order.get(item.get("chunk_id", ""), 9999),
        )
    )
    return evidence[:max(max_evidence, 1)]


async def _retrieve_memory_case_evidence_from_vertex(
    session,
    *,
    objective: str,
    assessment,
    query_terms: list[str],
    max_evidence: int,
    top_k: int,
) -> list[dict[str, Any]]:
    """Retrieve memory-case evidence via Vertex and hydrate from DB rows."""
    vector_service = VertexVectorSearchService()
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
        item = _build_memory_case_evidence(
            memory_case=case,
            query_terms=query_terms,
            risk_level=risk_level,
        )
        item["score"] = round(item["score"] + _score_bias_from_distance(neighbor.distance), 3)
        evidence.append(item)

    distance_order = {case_id: index for index, case_id in enumerate(ordered_ids)}
    evidence.sort(
        key=lambda item: (
            -item["score"],
            distance_order.get(item.get("memory_case_id", ""), 9999),
        )
    )
    return evidence[:max(max_evidence, 1)]


def _build_document_evidence(
    *,
    document,
    chunk,
    source: str,
    risk_level: str,
    query_terms: Iterable[str],
    score_bias: float,
) -> dict[str, Any]:
    searchable_text = " ".join(
        filter(
            None,
            [
                document.title,
                document.summary,
                document.document_type,
                chunk.content_text,
                " ".join(document.tags or []),
            ],
        )
    ).lower()
    matched_terms = [term for term in query_terms if term in searchable_text]
    score = score_bias + (len(matched_terms) * 0.85)
    if risk_level in searchable_text:
        score += 0.5
    if source == "threshold_doc" and any(term in searchable_text for term in ("threshold", "critical", "warning", "dsm")):
        score += 0.7
    if source == "sop_doc" and any(term in searchable_text for term in ("sop", "procedure", "guideline", "protocol")):
        score += 0.7

    snippet = _make_excerpt(chunk.content_text)
    citation = {
        "type": "knowledge_document",
        "source_uri": document.source_uri,
        "document_id": str(document.id),
        "chunk_id": str(chunk.id),
        "title": document.title,
    }
    metadata_filters = {
        "region": str((document.metadata_payload or {}).get("region_code") or "global"),
        "station": str((document.metadata_payload or {}).get("station_code") or "any"),
        "severity": str(risk_level or "unknown"),
        "crop": str((document.metadata_payload or {}).get("crop_group") or "any"),
        "time": str((document.metadata_payload or {}).get("effective_date") or "current"),
    }

    return {
        "rank": 0,
        "score": round(score, 3),
        "snippet": snippet,
        "citation": citation,
        "metadata_filters": metadata_filters,
        "evidence_type": "knowledge_document",
        "evidence_source": source,
        "title": document.title,
        "summary": document.summary,
        "content_excerpt": snippet,
        "document_id": str(document.id),
        "chunk_id": str(chunk.id),
        "source_uri": document.source_uri,
        "metadata": {
            "document_type": document.document_type,
            "matched_terms": matched_terms,
            "tags": document.tags or [],
        },
    }


def _build_case_evidence(
    *,
    incident,
    latest_plan,
    query_terms: Iterable[str],
    risk_level: str,
) -> dict[str, Any]:
    case_text = " ".join(
        filter(
            None,
            [
                incident.title,
                incident.description,
                latest_plan.summary if latest_plan is not None else None,
                latest_plan.objective if latest_plan is not None else None,
            ],
        )
    ).lower()
    matched_terms = [term for term in query_terms if term in case_text]
    score = 1.8 + (len(matched_terms) * 0.8)
    if risk_level in case_text:
        score += 0.5
    incident_status = _enum_value(incident.status)
    if incident_status in {IncidentStatus.RESOLVED.value, IncidentStatus.CLOSED.value}:
        score += 0.6
    if latest_plan is not None:
        score += 0.4

    opened_at = incident.opened_at
    age_days = max((datetime.now(UTC) - opened_at).days, 0)
    recency_bonus = max(0.0, 0.35 - min(age_days, 30) * 0.01)
    score += recency_bonus

    snippet = _make_excerpt(case_text)
    citation = {
        "type": "similar_case",
        "incident_id": str(incident.id),
        "risk_assessment_id": (
            str(incident.risk_assessment_id)
            if incident.risk_assessment_id is not None
            else None
        ),
        "plan_id": str(latest_plan.id) if latest_plan is not None else None,
        "opened_at": incident.opened_at.isoformat(),
    }
    metadata_filters = {
        "region": str(getattr(incident, "region_id", "unknown")),
        "station": str(getattr(incident, "station_id", "any")),
        "severity": _enum_value(incident.severity),
        "crop": "any",
        "time": incident.opened_at.date().isoformat(),
    }

    return {
        "rank": 0,
        "score": round(score, 3),
        "snippet": snippet,
        "citation": citation,
        "metadata_filters": metadata_filters,
        "evidence_type": "similar_case",
        "evidence_source": "past_similar_case",
        "title": incident.title,
        "summary": incident.description,
        "content_excerpt": snippet,
        "incident_id": str(incident.id),
        "risk_assessment_id": (
            str(incident.risk_assessment_id)
            if incident.risk_assessment_id is not None
            else None
        ),
        "metadata": {
            "severity": _enum_value(incident.severity),
            "status": incident_status,
            "opened_at": incident.opened_at.isoformat(),
            "plan_id": str(latest_plan.id) if latest_plan is not None else None,
            "matched_terms": matched_terms,
        },
    }


def _build_memory_case_evidence(
    *,
    memory_case,
    query_terms: Iterable[str],
    risk_level: str,
) -> dict[str, Any]:
    case_text = " ".join(
        filter(
            None,
            [
                memory_case.objective,
                memory_case.summary,
                str(memory_case.severity or ""),
                str(memory_case.outcome_class or ""),
                " ".join(memory_case.keywords or []),
            ],
        )
    ).lower()
    matched_terms = [term for term in query_terms if term in case_text]
    score = 2.1 + (len(matched_terms) * 0.75)
    if (memory_case.severity or "") == risk_level:
        score += 0.45
    if memory_case.outcome_class == "success":
        score += 0.65
    elif memory_case.outcome_class == "partial_success":
        score += 0.35

    snippet = _make_excerpt(memory_case.summary or case_text)
    citation = {
        "type": "memory_case",
        "memory_case_id": str(memory_case.id),
        "incident_id": str(memory_case.incident_id) if memory_case.incident_id is not None else None,
        "plan_id": str(memory_case.action_plan_id) if memory_case.action_plan_id is not None else None,
        "execution_id": (
            str(memory_case.action_execution_id)
            if memory_case.action_execution_id is not None
            else None
        ),
        "occurred_at": memory_case.occurred_at.isoformat(),
    }
    metadata_filters = {
        "region": str(memory_case.region_id),
        "station": str(memory_case.station_id) if memory_case.station_id is not None else "any",
        "severity": str(memory_case.severity or "unknown"),
        "crop": "any",
        "time": memory_case.occurred_at.date().isoformat(),
    }

    return {
        "rank": 0,
        "score": round(score, 3),
        "snippet": snippet,
        "citation": citation,
        "metadata_filters": metadata_filters,
        "evidence_type": "memory_case",
        "evidence_source": "memory_case",
        "title": "Memory case",
        "summary": memory_case.summary,
        "content_excerpt": snippet,
        "memory_case_id": str(memory_case.id),
        "metadata": {
            "outcome_class": memory_case.outcome_class,
            "legacy_status": memory_case.outcome_status_legacy,
            "severity": memory_case.severity,
            "matched_terms": matched_terms,
            "keywords": memory_case.keywords or [],
        },
    }


def _enum_value(value: Any) -> str:
    raw = getattr(value, "value", value)
    return str(raw)


def _infer_doc_source(document) -> str:
    document_type = (document.document_type or "").lower()
    tags = [str(tag).lower() for tag in (document.tags or [])]
    joined_tags = " ".join(tags)
    title = (document.title or "").lower()

    if any(term in document_type for term in ("sop", "procedure", "protocol")):
        return "sop_doc"
    if any(term in title for term in ("sop", "procedure", "protocol")):
        return "sop_doc"
    if any(term in joined_tags for term in ("sop", "procedure", "protocol")):
        return "sop_doc"

    if any(term in document_type for term in ("threshold", "policy", "rule")):
        return "threshold_doc"
    if any(term in title for term in ("threshold", "critical", "warning")):
        return "threshold_doc"
    if any(term in joined_tags for term in ("threshold", "critical", "warning", "dsm")):
        return "threshold_doc"

    return "knowledge_doc"


def _score_bias_from_distance(distance: float) -> float:
    # Lower distance means closer vector neighbor.
    normalized = max(0.05, 1.0 / (1.0 + max(distance, 0.0)))
    return round(2.8 * normalized, 3)


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


def _dedupe_evidence(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[dict[str, Any]] = []
    for item in items:
        if item["evidence_type"] == "knowledge_document":
            key = ("knowledge", f"{item.get('document_id')}::{item.get('chunk_id')}")
        else:
            key = ("case", str(item.get("incident_id")))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def _make_excerpt(text: str | None, *, limit: int = 280) -> str:
    if not text:
        return ""
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."
