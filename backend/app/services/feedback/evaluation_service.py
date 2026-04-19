"""Dedicated feedback evaluation service with normalized outcome taxonomy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from http import HTTPStatus
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.action import ActionExecution, ActionPlan, ExecutionBatch
from app.models.feedback import FeedbackSnapshot, OutcomeEvaluation
from app.repositories.action import ActionPlanRepository, ExecutionBatchRepository
from app.repositories.feedback import FeedbackSnapshotRepository, OutcomeEvaluationRepository
from app.repositories.sensor import SensorReadingRepository
from app.schemas.action import FeedbackEvaluation


@dataclass(slots=True)
class FeedbackLifecycleBundle:
    """Persisted feedback lifecycle artifacts for one evaluation run."""

    feedback: FeedbackEvaluation
    before_snapshot: FeedbackSnapshot
    after_snapshot: FeedbackSnapshot
    evaluation: OutcomeEvaluation


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


def _classify_feedback(
    *,
    baseline,
    latest,
) -> FeedbackEvaluation:
    if baseline is None or latest is None:
        return _build_feedback(
            outcome_class="inconclusive",
            status="insufficient_new_observation",
            summary="Không có cặp reading tương ứng để đánh giá kết quả vận hành.",
        )
    if latest.recorded_at <= baseline.recorded_at:
        return _build_feedback(
            outcome_class="inconclusive",
            status="insufficient_new_observation",
            baseline_salinity_dsm=baseline.salinity_dsm,
            latest_salinity_dsm=latest.salinity_dsm,
            summary="Chưa có reading mới hơn sau các hành động mô phỏng.",
        )

    delta = latest.salinity_dsm - baseline.salinity_dsm
    if delta < Decimal("0.00"):
        return _build_feedback(
            outcome_class="success",
            status="improved",
            baseline_salinity_dsm=baseline.salinity_dsm,
            latest_salinity_dsm=latest.salinity_dsm,
            delta_dsm=delta,
            summary="Độ mặn quan sát gần nhất đã giảm so với reading nền.",
        )
    if delta == Decimal("0.00"):
        return _build_feedback(
            outcome_class="partial_success",
            status="no_change",
            baseline_salinity_dsm=baseline.salinity_dsm,
            latest_salinity_dsm=latest.salinity_dsm,
            delta_dsm=delta,
            summary="Độ mặn quan sát gần nhất không thay đổi sau hành động mô phỏng.",
        )
    return _build_feedback(
        outcome_class="failed_execution",
        status="not_improved",
        baseline_salinity_dsm=baseline.salinity_dsm,
        latest_salinity_dsm=latest.salinity_dsm,
        delta_dsm=delta,
        summary="Độ mặn quan sát gần nhất chưa giảm sau hành động mô phỏng.",
    )


def _build_feedback_snapshot(
    *,
    batch: ExecutionBatch,
    plan: ActionPlan,
    execution: ActionExecution | None,
    snapshot_kind: str,
    reading,
    captured_at: datetime,
) -> FeedbackSnapshot:
    return FeedbackSnapshot(
        batch_id=batch.id,
        plan_id=plan.id,
        execution_id=execution.id if execution is not None else None,
        risk_assessment_id=plan.risk_assessment_id,
        station_id=(plan.risk_assessment.station_id if plan.risk_assessment is not None else None),
        reading_id=reading.id if reading is not None else None,
        snapshot_kind=snapshot_kind,
        captured_at=captured_at,
        reading_recorded_at=(reading.recorded_at if reading is not None else None),
        salinity_dsm=(reading.salinity_dsm if reading is not None else None),
        water_level_m=(reading.water_level_m if reading is not None else None),
        source="feedback-evaluator",
        payload={
            "snapshot_kind": snapshot_kind,
            "reading_source": "sensor_readings" if reading is not None else "missing",
        },
    )


async def _resolve_baseline_latest_readings(
    session: AsyncSession,
    plan: ActionPlan,
):
    if plan.risk_assessment is None or plan.risk_assessment.station_id is None:
        return None, None
    if plan.risk_assessment.based_on_reading_id is None:
        latest = await SensorReadingRepository(session).get_latest_for_station(
            plan.risk_assessment.station_id
        )
        return None, latest

    reading_repo = SensorReadingRepository(session)
    baseline = await reading_repo.get_with_station(plan.risk_assessment.based_on_reading_id)
    latest = await reading_repo.get_latest_for_station(plan.risk_assessment.station_id)
    return baseline, latest


async def persist_feedback_lifecycle(
    session: AsyncSession,
    *,
    batch: ExecutionBatch,
    plan: ActionPlan,
    execution: ActionExecution | None = None,
    evaluator_name: str = "feedback-evaluator",
) -> FeedbackLifecycleBundle:
    """Persist before/after snapshots and one outcome evaluation record."""
    baseline, latest = await _resolve_baseline_latest_readings(session, plan)
    feedback = _classify_feedback(baseline=baseline, latest=latest)

    captured_at = datetime.now(UTC)
    snapshot_repo = FeedbackSnapshotRepository(session)
    before_snapshot = await snapshot_repo.add(
        _build_feedback_snapshot(
            batch=batch,
            plan=plan,
            execution=execution,
            snapshot_kind="before",
            reading=baseline,
            captured_at=captured_at,
        )
    )
    after_snapshot = await snapshot_repo.add(
        _build_feedback_snapshot(
            batch=batch,
            plan=plan,
            execution=execution,
            snapshot_kind="after",
            reading=latest,
            captured_at=captured_at,
        )
    )

    evaluation = OutcomeEvaluation(
        batch_id=batch.id,
        plan_id=plan.id,
        execution_id=execution.id if execution is not None else None,
        before_snapshot_id=before_snapshot.id,
        after_snapshot_id=after_snapshot.id,
        evaluated_at=captured_at,
        outcome_class=feedback.outcome_class,
        status_legacy=feedback.status,
        baseline_salinity_dsm=feedback.baseline_salinity_dsm,
        latest_salinity_dsm=feedback.latest_salinity_dsm,
        delta_dsm=feedback.delta_dsm,
        summary=feedback.summary,
        replan_recommended=feedback.replan_recommended,
        replan_reason=feedback.replan_reason,
        evaluator_name=evaluator_name,
        payload={
            "taxonomy": "feedback_lifecycle_v1",
        },
    )
    evaluation = await OutcomeEvaluationRepository(session).add(evaluation)

    return FeedbackLifecycleBundle(
        feedback=feedback,
        before_snapshot=before_snapshot,
        after_snapshot=after_snapshot,
        evaluation=evaluation,
    )


async def evaluate_execution_feedback(
    session: AsyncSession,
    plan: ActionPlan,
    *,
    batch: ExecutionBatch | None = None,
    execution: ActionExecution | None = None,
    evaluator_name: str = "feedback-evaluator",
    persist_lifecycle: bool = False,
) -> FeedbackEvaluation:
    """Evaluate execution effect and map to normalized operational outcome classes."""
    if plan.risk_assessment is None or plan.risk_assessment.station_id is None:
        return _build_feedback(
            outcome_class="failed_plan",
            status="insufficient_new_observation",
            summary="Risk assessment chưa có ngữ cảnh trạm để đánh giá feedback.",
        )
    if plan.risk_assessment.based_on_reading_id is None:
        return _build_feedback(
            outcome_class="failed_plan",
            status="insufficient_new_observation",
            summary="Risk assessment chưa có reading nền để đánh giá feedback.",
        )

    baseline, latest = await _resolve_baseline_latest_readings(session, plan)
    feedback = _classify_feedback(baseline=baseline, latest=latest)
    if persist_lifecycle and batch is not None:
        persisted = await persist_feedback_lifecycle(
            session,
            batch=batch,
            plan=plan,
            execution=execution,
            evaluator_name=evaluator_name,
        )
        return persisted.feedback
    return feedback


async def evaluate_execution_batch_feedback(
    session: AsyncSession,
    *,
    batch_id: UUID,
    evaluator_name: str = "feedback-api",
) -> FeedbackLifecycleBundle:
    """Evaluate and persist feedback lifecycle artifacts for one execution batch."""
    batch = await ExecutionBatchRepository(session).get_with_executions(batch_id)
    if batch is None:
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="execution_batch_not_found",
            message=f"Execution batch '{batch_id}' was not found.",
        )

    plan = await ActionPlanRepository(session).get_with_assessment(batch.plan_id)
    if plan is None:
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="action_plan_not_found",
            message=f"Action plan '{batch.plan_id}' was not found.",
        )

    latest_execution = None
    if batch.executions:
        latest_execution = sorted(
            list(batch.executions),
            key=lambda item: (item.step_index, item.created_at),
        )[-1]

    return await persist_feedback_lifecycle(
        session,
        batch=batch,
        plan=plan,
        execution=latest_execution,
        evaluator_name=evaluator_name,
    )


async def get_latest_batch_feedback(
    session: AsyncSession,
    *,
    batch_id: UUID,
) -> FeedbackLifecycleBundle:
    """Return latest persisted feedback lifecycle artifacts for one execution batch."""
    evaluation = await OutcomeEvaluationRepository(session).get_latest_for_batch(batch_id)
    if evaluation is None:
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="feedback_evaluation_not_found",
            message=f"No feedback evaluation found for execution batch '{batch_id}'.",
        )

    feedback = FeedbackEvaluation(
        outcome_class=evaluation.outcome_class,
        status=evaluation.status_legacy,
        baseline_salinity_dsm=evaluation.baseline_salinity_dsm,
        latest_salinity_dsm=evaluation.latest_salinity_dsm,
        delta_dsm=evaluation.delta_dsm,
        summary=evaluation.summary,
        replan_recommended=evaluation.replan_recommended,
        replan_reason=evaluation.replan_reason,
    )
    return FeedbackLifecycleBundle(
        feedback=feedback,
        before_snapshot=evaluation.before_snapshot,
        after_snapshot=evaluation.after_snapshot,
        evaluation=evaluation,
    )
