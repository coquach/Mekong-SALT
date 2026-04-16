"""Dedicated feedback evaluation service with normalized outcome taxonomy."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action import ActionPlan
from app.repositories.sensor import SensorReadingRepository
from app.schemas.action import FeedbackEvaluation


def _build_feedback(
    *,
    outcome_class: str,
    status: str,
    summary: str,
    baseline_salinity_dsm: Decimal | None = None,
    latest_salinity_dsm: Decimal | None = None,
    delta_dsm: Decimal | None = None,
) -> FeedbackEvaluation:
    replan_recommended = outcome_class in {
        "failed_plan",
        "failed_execution",
        "partial_success",
        "inconclusive",
    }
    replan_reason = summary if replan_recommended else None
    return FeedbackEvaluation(
        outcome_class=outcome_class,
        status=status,
        baseline_salinity_dsm=baseline_salinity_dsm,
        latest_salinity_dsm=latest_salinity_dsm,
        delta_dsm=delta_dsm,
        summary=summary,
        replan_recommended=replan_recommended,
        replan_reason=replan_reason,
    )


async def evaluate_execution_feedback(
    session: AsyncSession,
    plan: ActionPlan,
) -> FeedbackEvaluation:
    """Evaluate execution effect and map to normalized operational outcome classes."""
    if plan.risk_assessment is None or plan.risk_assessment.station_id is None:
        return _build_feedback(
            outcome_class="failed_plan",
            status="insufficient_new_observation",
            summary="Risk assessment is missing station context for feedback evaluation.",
        )
    if plan.risk_assessment.based_on_reading_id is None:
        return _build_feedback(
            outcome_class="failed_plan",
            status="insufficient_new_observation",
            summary="Risk assessment is missing a baseline reading for feedback evaluation.",
        )

    reading_repo = SensorReadingRepository(session)
    baseline = await reading_repo.get_with_station(plan.risk_assessment.based_on_reading_id)
    latest = await reading_repo.get_latest_for_station(plan.risk_assessment.station_id)
    if baseline is None or latest is None:
        return _build_feedback(
            outcome_class="inconclusive",
            status="insufficient_new_observation",
            summary="No comparable readings were available for feedback evaluation.",
        )
    if latest.recorded_at <= baseline.recorded_at:
        return _build_feedback(
            outcome_class="inconclusive",
            status="insufficient_new_observation",
            baseline_salinity_dsm=baseline.salinity_dsm,
            latest_salinity_dsm=latest.salinity_dsm,
            summary="No newer sensor reading is available after the simulated actions.",
        )

    delta = latest.salinity_dsm - baseline.salinity_dsm
    if delta < Decimal("0.00"):
        return _build_feedback(
            outcome_class="success",
            status="improved",
            baseline_salinity_dsm=baseline.salinity_dsm,
            latest_salinity_dsm=latest.salinity_dsm,
            delta_dsm=delta,
            summary="Latest observed salinity is lower than the baseline reading.",
        )
    if delta == Decimal("0.00"):
        return _build_feedback(
            outcome_class="partial_success",
            status="no_change",
            baseline_salinity_dsm=baseline.salinity_dsm,
            latest_salinity_dsm=latest.salinity_dsm,
            delta_dsm=delta,
            summary="Latest observed salinity is unchanged after simulated actions.",
        )
    return _build_feedback(
        outcome_class="failed_execution",
        status="not_improved",
        baseline_salinity_dsm=baseline.salinity_dsm,
        latest_salinity_dsm=latest.salinity_dsm,
        delta_dsm=delta,
        summary="Latest observed salinity did not decrease after simulated actions.",
    )
