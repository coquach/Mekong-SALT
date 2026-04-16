"""Internal memory policy helpers for execution decision logs.

This module is intentionally internal-only and is not exposed through any API
endpoint. It centralizes memory promotion rules for agent decisions.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.models.decision import DecisionLog
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
