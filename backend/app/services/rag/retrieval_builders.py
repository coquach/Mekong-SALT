"""Evidence builders and scoring helpers for RAG retrieval lanes."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from app.models.enums import IncidentStatus


def build_document_evidence(
    *,
    document,
    chunk,
    source: str,
    risk_level: str,
    query_terms: Iterable[str],
    score_bias: float,
) -> dict[str, Any]:
    """Construct one static-document evidence item with heuristic scoring."""
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

    snippet = make_excerpt(chunk.content_text)
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
        "provenance": {
            "backend": "knowledge_document_repository",
            "entity_type": "knowledge_document",
            "entity_id": str(document.id),
            "chunk_id": str(chunk.id),
            "source_uri": document.source_uri,
        },
        "ranking_metadata": {
            "scoring_profile": "document_heuristic_v1",
            "score_bias": score_bias,
            "matched_terms": matched_terms,
            "matched_term_count": len(matched_terms),
        },
    }


def build_case_evidence(
    *,
    incident,
    latest_plan,
    query_terms: Iterable[str],
    risk_level: str,
) -> dict[str, Any]:
    """Construct one dynamic similar-incident evidence item."""
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
    incident_status = enum_value(incident.status)
    if incident_status in {IncidentStatus.RESOLVED.value, IncidentStatus.CLOSED.value}:
        score += 0.6
    if latest_plan is not None:
        score += 0.4

    opened_at = incident.opened_at
    age_days = max((datetime.now(UTC) - opened_at).days, 0)
    recency_bonus = max(0.0, 0.35 - min(age_days, 30) * 0.01)
    score += recency_bonus

    snippet = make_excerpt(case_text)
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
        "severity": enum_value(incident.severity),
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
            "severity": enum_value(incident.severity),
            "status": incident_status,
            "opened_at": incident.opened_at.isoformat(),
            "plan_id": str(latest_plan.id) if latest_plan is not None else None,
            "matched_terms": matched_terms,
        },
        "provenance": {
            "backend": "similar_case_repository",
            "entity_type": "incident",
            "entity_id": str(incident.id),
            "plan_id": str(latest_plan.id) if latest_plan is not None else None,
        },
        "ranking_metadata": {
            "scoring_profile": "similar_case_heuristic_v1",
            "recency_bonus": round(recency_bonus, 3),
            "matched_terms": matched_terms,
            "matched_term_count": len(matched_terms),
        },
    }


def build_memory_case_evidence(
    *,
    memory_case,
    query_terms: Iterable[str],
    risk_level: str,
) -> dict[str, Any]:
    """Construct one episodic memory-case evidence item."""
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

    snippet = make_excerpt(memory_case.summary or case_text)
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
        "provenance": {
            "backend": "memory_case_repository",
            "entity_type": "memory_case",
            "entity_id": str(memory_case.id),
            "incident_id": (
                str(memory_case.incident_id)
                if memory_case.incident_id is not None
                else None
            ),
        },
        "ranking_metadata": {
            "scoring_profile": "memory_case_heuristic_v1",
            "matched_terms": matched_terms,
            "matched_term_count": len(matched_terms),
        },
    }


def infer_doc_source(document) -> str:
    """Infer document evidence source class from type/title/tags."""
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


def score_bias_from_distance(distance: float) -> float:
    """Convert neighbor distance to additive score bias."""
    normalized = max(0.05, 1.0 / (1.0 + max(distance, 0.0)))
    return round(2.8 * normalized, 3)


def enum_value(value: Any) -> str:
    """Extract enum raw value safely."""
    raw = getattr(value, "value", value)
    return str(raw)


def make_excerpt(text: str | None, *, limit: int = 280) -> str:
    """Create compact excerpt for evidence snippets."""
    if not text:
        return ""
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."
