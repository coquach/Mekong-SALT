"""Feedback-driven replan request and handling services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.redis import RedisManager
from app.models.action import ActionPlan
from app.models.domain_event import DomainEvent
from app.models.enums import RiskLevel
from app.repositories.action import ActionPlanRepository
from app.schemas.agent import AgentPlanRequest
from app.schemas.action import FeedbackEvaluation
from app.schemas.replan import ReplanRequestedEventPayload
from app.schemas.risk import RiskEvaluationFilters
from app.services.agent_planning_service import AgentPlanBundle, generate_agent_plan
from app.services.domain_event_service import append_domain_event
from app.services.risk_service import evaluate_current_risk, resolve_target_reading

REPLAN_REQUEST_EVENT_TYPE = "monitoring.replan_requested"
REPLAN_COMPLETED_EVENT_TYPE = "monitoring.replan_completed"
PLANABLE_RISK_LEVELS = {RiskLevel.DANGER, RiskLevel.CRITICAL}


@dataclass(slots=True)
class ReplanRequestResult:
    """Summary of a queued or processed replan request."""

    requested_event: DomainEvent | None = None
    completed_event: DomainEvent | None = None
    plan_bundle: AgentPlanBundle | None = None
    lifecycle_status: str | None = None
    status: str = "skipped"
    reason: str | None = None


def should_replan_from_feedback(feedback_outcome_class: str | None) -> bool:
    """Return whether a feedback outcome should request a background replan."""
    normalized = str(feedback_outcome_class or "").strip().lower()
    return normalized in {
        "failed_execution",
        "failed_plan",
        "partial_success",
    }


async def queue_replan_request_from_feedback(
    session: AsyncSession,
    *,
    plan: ActionPlan,
    feedback: FeedbackEvaluation,
    execution_batch_id: UUID | None,
    trigger_source: str,
    settings: Settings | None = None,
    goal_id: UUID | None = None,
    goal_name: str | None = None,
) -> DomainEvent | None:
    """Persist a replan request event when policy allows it."""
    resolved_settings = settings or get_settings()
    max_attempts = max(
        0,
        int(getattr(resolved_settings, "active_monitoring_feedback_replan_max_attempts", 0)),
    )
    if max_attempts <= 0:
        return None
    if not should_replan_from_feedback(feedback.outcome_class):
        return None
    if plan.incident_id is None:
        return None

    requested_at = datetime.now(UTC)
    payload = ReplanRequestedEventPayload(
        summary="Background replan requested after execution feedback.",
        incident_id=plan.incident_id,
        region_id=plan.region_id,
        station_id=(
            plan.risk_assessment.station_id
            if plan.risk_assessment is not None
            else None
        ),
        risk_assessment_id=plan.risk_assessment_id,
        action_plan_id=plan.id,
        execution_batch_id=execution_batch_id,
        objective=plan.objective,
        feedback_outcome_class=feedback.outcome_class,
        feedback_status=feedback.status,
        feedback_summary=feedback.summary,
        replan_reason=feedback.replan_reason,
        requested_at=requested_at,
        attempt=1,
        trigger_source=trigger_source,
        goal_id=goal_id,
        goal_name=goal_name,
        dedupe_key=f"replan-request:{plan.id}:{feedback.outcome_class}:{feedback.status}",
    )
    return await append_domain_event(
        session,
        event_type=REPLAN_REQUEST_EVENT_TYPE,
        source=trigger_source,
        summary=payload.summary,
        payload=payload.model_dump(mode="json"),
        aggregate_type="incident",
        aggregate_id=plan.incident_id,
        region_id=plan.region_id,
        incident_id=plan.incident_id,
        action_plan_id=plan.id,
        execution_batch_id=execution_batch_id,
    )


async def handle_replan_requested_event(
    session: AsyncSession,
    *,
    event: DomainEvent,
    redis_manager: RedisManager | None,
    settings: Settings | None = None,
) -> ReplanRequestResult:
    """Handle one persisted replan request event."""
    resolved_settings = settings or get_settings()
    try:
        payload = ReplanRequestedEventPayload.model_validate(event.payload or {})
    except Exception as exc:
        return ReplanRequestResult(
            status="skipped",
            reason=f"Invalid replan payload: {exc}",
        )

    if payload.incident_id is None:
        return ReplanRequestResult(
            status="skipped",
            reason="Replan request is missing incident_id.",
        )

    plan_repo = ActionPlanRepository(session)
    source_plan = await plan_repo.get_with_assessment(payload.action_plan_id)
    if source_plan is None:
        return ReplanRequestResult(
            status="skipped",
            reason=f"Source plan '{payload.action_plan_id}' was not found.",
        )

    filters = RiskEvaluationFilters(
        station_id=payload.station_id,
        region_id=payload.region_id,
    )
    target_reading = await resolve_target_reading(session, filters)
    risk_bundle = await evaluate_current_risk(
        session,
        filters=filters,
        redis_manager=redis_manager,
        target_reading=target_reading,
        trigger_source="replan.worker.observe_risk",
        trigger_payload={
            "source_event_sequence": event.sequence,
            "source_plan_id": str(payload.action_plan_id),
            "feedback_outcome_class": payload.feedback_outcome_class,
            "trigger_source": payload.trigger_source,
        },
    )

    if risk_bundle.assessment.risk_level not in PLANABLE_RISK_LEVELS:
        completed_event = await append_domain_event(
            session,
            event_type=REPLAN_COMPLETED_EVENT_TYPE,
            source="replan-worker",
            summary="Replan request skipped because risk is below the plan gate.",
            payload={
                "source_event_sequence": event.sequence,
                "source_plan_id": str(payload.action_plan_id),
                "status": "skipped_risk_below_gate",
                "reason": (
                    f"Risk level '{risk_bundle.assessment.risk_level.value}' is below the plan gate."
                ),
                "risk_level": risk_bundle.assessment.risk_level.value,
                "feedback_outcome_class": payload.feedback_outcome_class,
            },
            aggregate_type="incident",
            aggregate_id=payload.incident_id,
            region_id=payload.region_id,
            incident_id=payload.incident_id,
            action_plan_id=payload.action_plan_id,
        )
        await session.commit()
        return ReplanRequestResult(
            completed_event=completed_event,
            risk_bundle=risk_bundle,
            status="skipped_risk_below_gate",
            reason=(
                f"Risk level '{risk_bundle.assessment.risk_level.value}' is below the plan gate."
            ),
        )

    existing_plan = await plan_repo.get_open_for_incident(payload.incident_id)
    if existing_plan is not None and existing_plan.id != source_plan.id:
        completed_event = await append_domain_event(
            session,
            event_type=REPLAN_COMPLETED_EVENT_TYPE,
            source="replan-worker",
            summary="Replan request skipped because another open plan already exists.",
            payload={
                "source_event_sequence": event.sequence,
                "source_plan_id": str(payload.action_plan_id),
                "status": "skipped_existing_open_plan",
                "reason": "A different open plan already exists for this incident.",
                "open_plan_id": str(existing_plan.id),
                "feedback_outcome_class": payload.feedback_outcome_class,
            },
            aggregate_type="incident",
            aggregate_id=payload.incident_id,
            region_id=payload.region_id,
            incident_id=payload.incident_id,
            action_plan_id=existing_plan.id,
        )
        await session.commit()
        return ReplanRequestResult(
            completed_event=completed_event,
            risk_bundle=risk_bundle,
            status="skipped_existing_open_plan",
            reason="A different open plan already exists for this incident.",
        )

    plan_bundle = await generate_agent_plan(
        session,
        payload=AgentPlanRequest(
            station_id=payload.station_id,
            region_id=payload.region_id,
            incident_id=payload.incident_id,
            objective=payload.objective,
        ),
        redis_manager=redis_manager,
        risk_bundle=risk_bundle,
        trigger_source="replan.worker.generate_plan",
        trigger_payload={
            "source_event_sequence": event.sequence,
            "source_plan_id": str(payload.action_plan_id),
            "feedback_outcome_class": payload.feedback_outcome_class,
            "feedback_status": payload.feedback_status,
            "feedback_summary": payload.feedback_summary,
        },
    )
    from app.orchestration.lifecycle_graph import advance_plan_with_lifecycle_graph

    lifecycle_kwargs: dict[str, Any] = {
        "session": session,
        "plan": plan_bundle.plan,
        "settings": resolved_settings,
    }
    if redis_manager is not None:
        lifecycle_kwargs["redis_manager"] = redis_manager
    lifecycle_result = await advance_plan_with_lifecycle_graph(**lifecycle_kwargs)
    completed_event = await append_domain_event(
        session,
        event_type=REPLAN_COMPLETED_EVENT_TYPE,
        source="replan-worker",
        summary="Background replan completed.",
        payload={
            "source_event_sequence": event.sequence,
            "source_plan_id": str(payload.action_plan_id),
            "status": "completed",
            "new_plan_id": str(plan_bundle.plan.id),
            "lifecycle_status": lifecycle_result.status,
            "reason": lifecycle_result.reason,
            "risk_level": risk_bundle.assessment.risk_level.value,
            "feedback_outcome_class": payload.feedback_outcome_class,
        },
        aggregate_type="incident",
        aggregate_id=payload.incident_id,
        region_id=payload.region_id,
        incident_id=payload.incident_id,
        action_plan_id=plan_bundle.plan.id,
    )
    await session.commit()

    return ReplanRequestResult(
        completed_event=completed_event,
        plan_bundle=plan_bundle,
        lifecycle_status=lifecycle_result.status,
        status="completed",
    )
