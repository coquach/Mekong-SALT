"""Dynamic similar-incident retrieval lane."""

from __future__ import annotations

from app.repositories.action import ActionPlanRepository
from app.repositories.knowledge import SimilarCaseRepository
from app.services.rag.retrieval_builders import build_case_evidence


async def retrieve_similar_case_lane(
    session,
    *,
    assessment,
    query_terms: list[str],
    risk_level: str,
) -> list[dict]:
    """Retrieve dynamic similar-incident evidence from operational DB records."""
    case_repo = SimilarCaseRepository(session)
    action_repo = ActionPlanRepository(session)
    similar_incidents = await case_repo.list_similar_incidents(
        region_id=assessment.region_id,
        severity=assessment.risk_level,
        exclude_assessment_id=getattr(assessment, "id", None),
        limit=4,
    )

    evidence: list[dict] = []
    for incident in similar_incidents:
        latest_plan = await action_repo.get_latest_for_incident(incident.id)
        evidence.append(
            build_case_evidence(
                incident=incident,
                latest_plan=latest_plan,
                query_terms=query_terms,
                risk_level=risk_level,
            )
        )
    return evidence
