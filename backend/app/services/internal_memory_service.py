"""Internal memory policy helpers for execution decision logs.

This module is intentionally internal-only and is not exposed through any API
endpoint. It centralizes memory promotion rules for agent decisions.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.models.decision import DecisionLog
from app.models.memory_case import MemoryCase
from app.models.enums import ActionType, DecisionActorType
from app.schemas.action import FeedbackEvaluation


def build_execution_decision_log(
    *,
    region_id: UUID,
    risk_assessment_id: UUID,
    action_plan_id: UUID,
    action_execution_id: UUID,
    logged_at: datetime,
    step_index: int,
    action_type: ActionType,
    title: str,
    result_summary: str | None,
) -> DecisionLog:
    """Create a per-step execution decision log with memory disabled."""
    return DecisionLog(
        region_id=region_id,
        risk_assessment_id=risk_assessment_id,
        action_plan_id=action_plan_id,
        action_execution_id=action_execution_id,
        logged_at=logged_at,
        actor_type=DecisionActorType.AGENT,
        actor_name="simulated-execution-engine",
        summary=f"Simulated action executed: {action_type.value}",
        outcome="simulated",
        details={
            "step_index": step_index,
            "action_type": action_type.value,
            "title": title,
            "result_summary": result_summary,
        },
        store_as_memory=False,
    )


def build_feedback_decision_log(
    *,
    region_id: UUID,
    risk_assessment_id: UUID,
    action_plan_id: UUID,
    action_execution_id: UUID | None,
    logged_at: datetime,
    feedback: FeedbackEvaluation,
) -> DecisionLog:
    """Create the post-execution feedback log and apply memory promotion policy."""
    return DecisionLog(
        region_id=region_id,
        risk_assessment_id=risk_assessment_id,
        action_plan_id=action_plan_id,
        action_execution_id=action_execution_id,
        logged_at=logged_at,
        actor_type=DecisionActorType.SYSTEM,
        actor_name="feedback-evaluator",
        summary="Simulated execution feedback evaluated.",
        outcome=feedback.outcome_class,
        details=feedback.model_dump(mode="json"),
        store_as_memory=feedback.outcome_class == "success",
    )


def build_feedback_memory_case(
    *,
    region_id: UUID,
    station_id: UUID | None,
    risk_assessment_id: UUID | None,
    incident_id: UUID | None,
    action_plan_id: UUID | None,
    action_execution_id: UUID | None,
    decision_log_id: UUID | None,
    objective: str | None,
    severity: str | None,
    feedback: FeedbackEvaluation,
    context_payload: dict,
    action_payload: dict,
    occurred_at: datetime,
) -> MemoryCase:
    """Create a persistent memory case row for future retrieval-time reuse."""
    keywords = _derive_case_keywords(
        objective=objective,
        severity=severity,
        outcome_class=feedback.outcome_class,
        action_payload=action_payload,
    )
    return MemoryCase(
        region_id=region_id,
        station_id=station_id,
        risk_assessment_id=risk_assessment_id,
        incident_id=incident_id,
        action_plan_id=action_plan_id,
        action_execution_id=action_execution_id,
        decision_log_id=decision_log_id,
        objective=objective,
        severity=severity,
        outcome_class=feedback.outcome_class,
        outcome_status_legacy=feedback.status,
        summary=feedback.summary,
        context_payload=context_payload,
        action_payload=action_payload,
        outcome_payload=feedback.model_dump(mode="json"),
        keywords=keywords,
        occurred_at=occurred_at,
    )


def _derive_case_keywords(
    *,
    objective: str | None,
    severity: str | None,
    outcome_class: str,
    action_payload: dict,
) -> list[str]:
    """Build compact keyword tokens for memory-case filtering."""
    keywords: list[str] = []
    if objective:
        keywords.extend(
            token.lower()
            for token in objective.split()
            if len(token) > 2
        )
    if severity:
        keywords.append(severity.lower())
    keywords.append(outcome_class.lower())

    for step in action_payload.get("steps", []):
        action_type = str(step.get("action_type") or "").strip().lower()
        if action_type:
            keywords.append(action_type)

    deduped: list[str] = []
    for keyword in keywords:
        if keyword not in deduped:
            deduped.append(keyword)
    return deduped[:24]
