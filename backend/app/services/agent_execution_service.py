"""Simulated execution and feedback services."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus
import logging
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.execution_policy import validate_execution_plan
from app.core.salinity_units import dsm_to_gl
from app.core.exceptions import AppException
from app.db.redis import RedisManager
from app.models.action import ActionExecution, ActionPlan, ExecutionBatch
from app.models.audit import ActionOutcome
from app.models.decision import DecisionLog
from app.models.enums import ActionPlanStatus, ActionType, AuditEventType, ExecutionStatus, IncidentStatus
from app.repositories.action import ActionExecutionRepository, ActionPlanRepository, ExecutionBatchRepository
from app.repositories.decision import DecisionLogRepository
from app.repositories.memory_case import MemoryCaseRepository
from app.repositories.ops import ActionOutcomeRepository
from app.repositories.region import RegionRepository
from app.schemas.action import (
    ActionLogCollection,
    ActionLogEntry,
    FeedbackEvaluation,
    SimulatedExecutionRequest,
)
from app.schemas.graph import build_execution_graph_from_batch
from app.services.gate_command_driver import GATE_ACTION_TYPES, SimulatedGateCommandDriver
from app.services.feedback.evaluation_service import evaluate_execution_feedback
from app.services.graph_stream_service import publish_graph_transition

from app.services.memory_case_vector_service import MemoryCaseVectorService
from app.services.internal_memory_service import (
    build_execution_decision_log,
    build_feedback_decision_log,
    build_feedback_memory_case,
)
from app.services.audit_service import write_audit_log
from app.services.db import append_domain_event_and_dispatch
from app.services.notify import get_domain_event_notification_dispatcher
from app.services.replan_service import queue_replan_request_from_feedback


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SimulatedExecutionBundle:
    """Aggregate result returned after simulated execution."""

    batch: ExecutionBatch
    plan: ActionPlan
    executions: list[ActionExecution]
    feedback: FeedbackEvaluation
    decision_logs: list[DecisionLog]
    outcomes: list[ActionOutcome]
    idempotent_replay: bool = False


async def execute_simulated_plan(
    session: AsyncSession,
    *,
    payload: SimulatedExecutionRequest,
    actor_name: str = "operator",
    redis_manager: RedisManager | None = None,
) -> SimulatedExecutionBundle:
    """Execute a validated plan in simulated mode only."""
    logger.info(
        "Starting simulated execution",
        extra={
            "action_plan_id": str(payload.action_plan_id),
            "idempotency_key": payload.idempotency_key,
            "actor_name": actor_name,
        },
    )
    plan_repo = ActionPlanRepository(session)
    batch_repo = ExecutionBatchRepository(session)
    execution_repo = ActionExecutionRepository(session)
    decision_repo = DecisionLogRepository(session)
    outcome_repo = ActionOutcomeRepository(session)

    if payload.idempotency_key is not None:
        existing_batch = await batch_repo.get_by_idempotency_key(payload.idempotency_key)
        if existing_batch is not None:
            if existing_batch.plan_id != payload.action_plan_id:
                raise AppException(
                    status_code=HTTPStatus.CONFLICT,
                    code="idempotency_key_conflict",
                    message="Provided idempotency key is already used for another action plan.",
                )

            plan = await plan_repo.get_with_assessment(existing_batch.plan_id)
            if plan is None:
                raise AppException(
                    status_code=HTTPStatus.NOT_FOUND,
                    code="action_plan_not_found",
                    message=f"Action plan '{existing_batch.plan_id}' was not found.",
                )
            executions = await execution_repo.list_for_batch(existing_batch.id)
            decision_logs = await decision_repo.list_for_execution_ids(
                [execution.id for execution in executions]
            ) if executions else []
            logger.info(
                "Reused simulated execution batch from idempotency key",
                extra={
                    "action_plan_id": str(payload.action_plan_id),
                    "execution_batch_id": str(existing_batch.id),
                    "idempotency_key": payload.idempotency_key,
                },
            )
            feedback = FeedbackEvaluation(
                outcome_class="inconclusive",
                status="insufficient_new_observation",
                summary="Execution batch was returned from an existing idempotency key.",
                replan_recommended=True,
                replan_reason="Execution batch was returned from an existing idempotency key.",
            )
            return SimulatedExecutionBundle(
                batch=existing_batch,
                plan=plan,
                executions=executions,
                feedback=feedback,
                decision_logs=decision_logs,
                outcomes=[],
                idempotent_replay=True,
            )

    plan = await plan_repo.get_with_assessment(payload.action_plan_id)
    if plan is None:
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="action_plan_not_found",
            message=f"Action plan '{payload.action_plan_id}' was not found.",
        )

    steps = validate_execution_plan(plan)
    logger.info(
        "Validated plan for simulated execution",
        extra={
            "action_plan_id": str(plan.id),
            "step_count": len(steps),
            "incident_id": str(plan.incident_id) if plan.incident_id is not None else None,
        },
    )
    now = datetime.now(UTC)
    batch = ExecutionBatch(
        plan_id=plan.id,
        region_id=plan.region_id,
        status=ExecutionStatus.RUNNING,
        simulated=True,
        started_at=now,
        completed_at=None,
        idempotency_key=payload.idempotency_key,
        requested_by=actor_name,
    )
    await batch_repo.add(batch)

    executions: list[ActionExecution] = []
    decision_logs: list[DecisionLog] = []
    outcomes: list[ActionOutcome] = []
    gate_driver = SimulatedGateCommandDriver()
    if plan.incident is not None:
        plan.incident.status = IncidentStatus.EXECUTING

    for step in steps:
        logger.info(
            "Executing simulated plan step",
            extra={
                "action_plan_id": str(plan.id),
                "execution_batch_id": str(batch.id),
                "step_index": step.step_index,
                "action_type": step.action_type.value,
                "target_gate_code": step.target_gate_code,
            },
        )
        result_summary = _build_execution_summary(step.action_type)
        result_payload: dict[str, object] = {
            "title": step.title,
            "instructions": step.instructions,
            "rationale": step.rationale,
            "simulated": True,
        }
        if step.action_type in GATE_ACTION_TYPES:
            gate_result = await gate_driver.execute(
                session,
                plan=plan,
                step=step,
                actor_name=actor_name,
            )
            result_summary = gate_result.summary
            result_payload = {
                **gate_result.payload,
                "title": step.title,
                "instructions": step.instructions,
                "rationale": step.rationale,
                "step_index": step.step_index,
                "action_type": step.action_type.value,
                "target_gate_code": step.target_gate_code,
            }

        execution = ActionExecution(
            plan_id=plan.id,
            batch_id=batch.id,
            region_id=plan.region_id,
            action_type=step.action_type,
            status=ExecutionStatus.SUCCEEDED,
            simulated=True,
            step_index=step.step_index,
            started_at=now,
            completed_at=now,
            result_summary=result_summary,
            result_payload=result_payload,
            idempotency_key=(
                f"{payload.idempotency_key}:{step.step_index}"
                if payload.idempotency_key is not None
                else f"{batch.id}:{step.step_index}"
            ),
            requested_by=actor_name,
        )
        await execution_repo.add(execution)
        executions.append(execution)

        decision_log = build_execution_decision_log(
            region_id=plan.region_id,
            risk_assessment_id=plan.risk_assessment_id,
            action_plan_id=plan.id,
            action_execution_id=execution.id,
            logged_at=now,
            step_index=step.step_index,
            action_type=step.action_type,
            title=step.title,
            result_summary=execution.result_summary,
        )
        await decision_repo.add(decision_log)
        decision_logs.append(decision_log)
        await write_audit_log(
            session,
            event_type=AuditEventType.EXECUTION,
            actor_name=actor_name,
            region_id=plan.region_id,
            incident_id=plan.incident_id,
            action_plan_id=plan.id,
            action_execution_id=execution.id,
            summary=f"Simulated action executed: {step.action_type.value}.",
            payload=execution.result_payload,
        )
        await _emit_execution_batch_transition(
            redis_manager,
            batch=batch,
            plan=plan,
            executions=executions,
            node=f"step-{step.step_index}",
            status="active",
            summary=result_summary,
            step_index=step.step_index,
            plan_incident_id=plan.incident_id,
        )

    feedback = await evaluate_execution_feedback(
        session,
        plan,
        batch=batch,
        execution=executions[-1] if executions else None,
        evaluator_name="execution-agent",
        persist_lifecycle=True,
    )
    if executions:
        outcome = ActionOutcome(
            execution_id=executions[-1].id,
            recorded_at=datetime.now(UTC),
            pre_metrics={
                "baseline_salinity_dsm": str(feedback.baseline_salinity_dsm)
                if feedback.baseline_salinity_dsm is not None
                else None,
                "baseline_salinity_gl": (
                    str(dsm_to_gl(feedback.baseline_salinity_dsm))
                    if feedback.baseline_salinity_dsm is not None
                    else None
                ),
            },
            post_metrics={
                "latest_salinity_dsm": str(feedback.latest_salinity_dsm)
                if feedback.latest_salinity_dsm is not None
                else None,
                "latest_salinity_gl": (
                    str(dsm_to_gl(feedback.latest_salinity_dsm))
                    if feedback.latest_salinity_dsm is not None
                    else None
                ),
                "delta_dsm": str(feedback.delta_dsm) if feedback.delta_dsm is not None else None,
                "delta_gl": (
                    str(dsm_to_gl(feedback.delta_dsm))
                    if feedback.delta_dsm is not None
                    else None
                ),
                "legacy_status": feedback.status,
            },
            status=feedback.outcome_class,
            summary=feedback.summary,
        )
        await outcome_repo.add(outcome)
        outcomes.append(outcome)
    feedback_log = build_feedback_decision_log(
        region_id=plan.region_id,
        risk_assessment_id=plan.risk_assessment_id,
        action_plan_id=plan.id,
        action_execution_id=executions[-1].id if executions else None,
        logged_at=datetime.now(UTC),
        feedback=feedback,
    )
    await decision_repo.add(feedback_log)
    decision_logs.append(feedback_log)

    try:
        await queue_replan_request_from_feedback(
            session,
            plan=plan,
            feedback=feedback,
            execution_batch_id=batch.id,
            trigger_source="execution-service.feedback",
        )
    except Exception:
        logger.exception(
            "Failed to queue background replan request",
            extra={
                "action_plan_id": str(plan.id),
                "execution_batch_id": str(batch.id),
                "outcome_class": feedback.outcome_class,
            },
        )

    await append_domain_event_and_dispatch(
        session,
        event_type="notification.execution_summary",
        source="execution-service",
        summary="Tổng kết mô phỏng đã sẵn sàng.",
        payload={
            "event": "execution_summary",
            "subject": "Thông báo kết quả mô phỏng",
            "message": _build_execution_summary_notification_message(
                plan=plan,
                feedback=feedback,
                executions=executions,
            ),
            "details": {
                "outcome_class": feedback.outcome_class,
                "replan_recommended": feedback.replan_recommended,
                "action_summary": _summarize_execution_steps(executions),
            },
        },
        aggregate_type="incident" if plan.incident_id is not None else "action_plan",
        aggregate_id=plan.incident_id if plan.incident_id is not None else plan.id,
        region_id=plan.region_id,
        incident_id=plan.incident_id,
        action_plan_id=plan.id,
        execution_batch_id=batch.id,
        dispatcher=get_domain_event_notification_dispatcher(),
    )

  
    memory_case = build_feedback_memory_case(
        region_id=plan.region_id,
        station_id=(plan.risk_assessment.station_id if plan.risk_assessment is not None else None),
        risk_assessment_id=plan.risk_assessment_id,
        incident_id=plan.incident_id,
        action_plan_id=plan.id,
        action_execution_id=(executions[-1].id if executions else None),
        decision_log_id=feedback_log.id,
        objective=plan.objective,
        severity=(
            plan.risk_assessment.risk_level.value
            if plan.risk_assessment is not None
            else None
        ),
        feedback=feedback,
        context_payload={
            "incident_id": str(plan.incident_id) if plan.incident_id is not None else None,
            "risk_assessment_id": str(plan.risk_assessment_id),
            "weather_linked": plan.risk_assessment.based_on_weather_id is not None
            if plan.risk_assessment is not None
            else False,
        },
        action_payload={
            "steps": plan.plan_steps,
            "execution_count": len(executions),
            "batch_id": str(batch.id),
        },
        occurred_at=datetime.now(UTC),
    )
    memory_case_repo = MemoryCaseRepository(session)
    if await memory_case_repo.is_table_ready():
        try:
            await memory_case_repo.add(memory_case)
            await asyncio.wait_for(
                MemoryCaseVectorService().upsert_memory_case(memory_case),
                timeout=2.5,
            )
        except SQLAlchemyError:
            # Keep execution path resilient during phased rollout before migration is applied.
            pass
        except Exception:
            # Vector indexing is best-effort and must not fail execution pipeline.
            pass

    plan.status = ActionPlanStatus.SIMULATED
    batch.status = ExecutionStatus.SUCCEEDED
    batch.completed_at = datetime.now(UTC)
    if plan.incident is not None:
        plan.incident.status = (
            IncidentStatus.RESOLVED
            if feedback.outcome_class == "success"
            else IncidentStatus.EXECUTING
        )
    await session.commit()

    await _emit_execution_batch_transition(
        redis_manager,
        batch=batch,
        plan=plan,
        executions=executions,
        node="feedback",
        status="completed",
        summary=feedback.summary,
        feedback=feedback,
        plan_incident_id=plan.incident_id,
    )

    for execution in executions:
        await session.refresh(execution)
    for decision_log in decision_logs:
        await session.refresh(decision_log)
    for outcome in outcomes:
        await session.refresh(outcome)
    await session.refresh(batch)
    await session.refresh(plan)

    logger.info(
        "Simulated execution completed",
        extra={
            "action_plan_id": str(plan.id),
            "execution_batch_id": str(batch.id),
            "execution_count": len(executions),
            "outcome_class": feedback.outcome_class,
            "plan_status": plan.status.value,
        },
    )

    return SimulatedExecutionBundle(
        batch=batch,
        plan=plan,
        executions=executions,
        feedback=feedback,
        decision_logs=decision_logs,
        outcomes=outcomes,
    )


async def _emit_execution_batch_transition(
    redis_manager: RedisManager | None,
    *,
    batch: ExecutionBatch,
    plan: ActionPlan,
    executions: list[ActionExecution],
    node: str,
    status: str,
    summary: str | None,
    step_index: int | None = None,
    feedback: FeedbackEvaluation | None = None,
    plan_incident_id: UUID | None = None,
) -> None:
    """Best-effort stream update for the execution batch graph."""
    if redis_manager is None:
        return

    batch_payload = {
        "id": str(batch.id),
        "plan_id": str(batch.plan_id),
        "region_id": str(batch.region_id),
        "status": batch.status.value,
        "simulated": batch.simulated,
        "requested_by": batch.requested_by,
        "idempotency_key": batch.idempotency_key,
        "started_at": batch.started_at.isoformat() if batch.started_at is not None else None,
        "completed_at": batch.completed_at.isoformat() if batch.completed_at is not None else None,
        "step_count": len(executions),
    }
    execution_payloads = [
        {
            "id": str(execution.id),
            "created_at": execution.created_at.isoformat(),
            "updated_at": execution.updated_at.isoformat(),
            "plan_id": str(execution.plan_id),
            "batch_id": str(execution.batch_id) if execution.batch_id is not None else None,
            "region_id": str(execution.region_id),
            "action_type": execution.action_type.value,
            "status": execution.status.value,
            "simulated": execution.simulated,
            "step_index": execution.step_index,
            "started_at": execution.started_at.isoformat() if execution.started_at is not None else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at is not None else None,
            "result_summary": execution.result_summary,
            "result_payload": execution.result_payload,
            "idempotency_key": execution.idempotency_key,
            "requested_by": execution.requested_by,
        }
        for execution in executions
    ]
    feedback_payload = feedback.model_dump(mode="json") if feedback is not None else None
    graph_snapshot = build_execution_graph_from_batch(
        batch_payload,
        execution_payloads,
        feedback=feedback_payload,
        metadata={
            "plan_id": str(plan.id),
            "region_id": str(plan.region_id),
            "incident_id": str(plan_incident_id) if plan_incident_id is not None else None,
            "batch_id": str(batch.id),
        },
    )
    await publish_graph_transition(
        redis_manager,
        graph_type="execution_batch",
        node=node,
        status=status,
        details={
            "step_index": step_index,
            "batch_status": batch.status.value,
            "execution_count": len(executions),
        },
        summary=summary,
        plan_id=plan.id,
        incident_id=plan_incident_id,
        execution_batch_id=batch.id,
        graph_snapshot=graph_snapshot,
    )


async def list_action_logs(
    session: AsyncSession,
    *,
    plan_id: UUID | None = None,
    region_id: UUID | None = None,
    region_code: str | None = None,
    limit: int = 50,
) -> ActionLogCollection:
    """Return simulated execution logs with linked decision entries."""
    resolved_region_id = region_id
    if region_code is not None:
        region = await RegionRepository(session).get_by_code(region_code)
        if region is None:
            raise AppException(
                status_code=HTTPStatus.NOT_FOUND,
                code="region_not_found",
                message=f"Region '{region_code}' was not found.",
            )
        resolved_region_id = region.id

    execution_repo = ActionExecutionRepository(session)
    executions = await execution_repo.list_for_logs(
        region_id=resolved_region_id,
        plan_id=plan_id,
        limit=limit,
    )
    decision_logs = await DecisionLogRepository(session).list_for_execution_ids(
        [execution.id for execution in executions]
    )
    latest_log_by_execution: dict[UUID, DecisionLog] = {}
    for log in decision_logs:
        if log.action_execution_id is not None and log.action_execution_id not in latest_log_by_execution:
            latest_log_by_execution[log.action_execution_id] = log

    items = [
        ActionLogEntry(
            execution=execution,
            decision_log=latest_log_by_execution.get(execution.id),
        )
        for execution in executions
    ]
    return ActionLogCollection(items=items, count=len(items))


def _build_execution_summary(action_type) -> str:
    """Return a fixed summary for each simulated action type."""
    summaries = {
        "close_gate": "Đã chấp nhận lệnh đóng cống mô phỏng.",
        "open_gate": "Đã chấp nhận lệnh mở cống mô phỏng.",
        "start_pump": "Đã chấp nhận lệnh khởi động bơm mô phỏng.",
        "stop_pump": "Đã chấp nhận lệnh dừng bơm mô phỏng.",
        "send_alert": "Đã gửi cảnh báo mô phỏng tới các bên liên quan.",
        "notify-farmers": "Đã gửi thông báo hướng dẫn mô phỏng tới nông dân.",
        "wait-safe-window": "Đã áp dụng khoảng chờ mô phỏng trong khi chờ điều kiện an toàn hơn.",
        "close-gate-simulated": "Đã hoàn tất kịch bản đóng cống tạm thời mô phỏng.",
        "start-pump-simulated": "Đã hoàn tất kịch bản khởi động bơm mô phỏng.",
    }
    return summaries[action_type.value]


def _summarize_execution_steps(executions: list[ActionExecution], max_items: int = 3) -> str:
    """Build a short step synopsis for the final summary notification."""
    steps: list[str] = []
    for execution in executions[:max_items]:
        summary = execution.result_summary or execution.action_type.value
        steps.append(str(summary).strip().rstrip(".。!！?？"))
    return " -> ".join(step for step in steps if step)


def _build_execution_summary_notification_message(
    *,
    plan: ActionPlan,
    feedback: FeedbackEvaluation,
    executions: list[ActionExecution],
) -> str:
    """Build a short citizen-friendly notification for the execution result."""
    outcome_label = {
        "success": "thành công",
        "partial_success": "thành công một phần",
        "failed_execution": "thực thi thất bại",
        "failed_plan": "kế hoạch thất bại",
        "inconclusive": "chưa đủ dữ liệu để kết luận",
    }.get(feedback.outcome_class, feedback.outcome_class)
    action_summary = _summarize_execution_steps(executions)
    effectiveness_reason = _build_execution_effectiveness_reason(feedback=feedback, executions=executions)
    parts = [
        f"Hệ thống đã hoàn tất mô phỏng cho mục tiêu: {plan.objective}.",
        f"Kết quả mô phỏng: {outcome_label}.",
    ]
    if action_summary:
        parts.append(f"Các bước đã thực hiện: {action_summary}.")
    if effectiveness_reason:
        parts.append(effectiveness_reason)
    if feedback.replan_recommended:
        parts.append("Hệ thống đề xuất xem xét lập lại kế hoạch để an toàn hơn.")
    parts.append("Nếu cần, bạn có thể mở bảng điều khiển để xem chi tiết.")
    return " ".join(parts)


def _build_execution_effectiveness_reason(
    *,
    feedback: FeedbackEvaluation,
    executions: list[ActionExecution],
) -> str:
    """Explain why the executed plan is considered effective in plain language."""
    executed_step_count = len(executions)
    action_summary = _summarize_execution_steps(executions)

    if feedback.outcome_class == "success":
        return (
            f"Điều này cho thấy phương án mô phỏng đang đi đúng hướng, vì hệ thống đã thực hiện đủ {executed_step_count} bước chính "
            f"và duy trì chuỗi hành động theo đúng trình tự. Cách làm này giúp phản ứng sớm hơn và giảm nguy cơ để tình trạng xấu lan rộng."
        )

    if feedback.outcome_class == "partial_success":
        return (
            "Kết quả này cho thấy hệ thống đã xử lý được một phần vấn đề, tức là các bước quan trọng đã đi đúng hướng nhưng vẫn còn điểm cần tối ưu. "
            "Điều đó hữu ích vì nó giúp giảm một phần áp lực vận hành trong khi vẫn để lại không gian điều chỉnh an toàn hơn."
        )

    if feedback.outcome_class == "inconclusive":
        if action_summary:
            return (
                f"Mặc dù kết quả chưa đủ để kết luận, hệ thống vẫn đã hoàn thành chuỗi hành động chính là {action_summary}. "
                "Điều này chứng minh quy trình phản ứng đã chạy đến cuối luồng, nhưng cần thêm dữ liệu quan sát để đánh giá hiệu quả thực tế chính xác hơn."
            )
        return (
            "Mặc dù kết quả chưa đủ để kết luận, hệ thống vẫn đã chạy xong luồng mô phỏng cần thiết. "
            "Điều này cho thấy quy trình phản ứng đã hoạt động, nhưng cần thêm dữ liệu để chứng minh hiệu quả cuối cùng."
        )

    if feedback.outcome_class == "failed_execution":
        return (
            "Kết quả này cho thấy phương án hiện tại chưa vận hành như mong muốn, vì vậy cần xem lại điểm nghẽn trước khi áp dụng rộng hơn. "
            "Dù vậy, việc phát hiện sớm vấn đề cũng có giá trị vì nó giúp tránh triển khai một phương án chưa ổn định ra thực tế."
        )

    if feedback.outcome_class == "failed_plan":
        return (
            "Kế hoạch chưa đạt yêu cầu ở bước đánh giá, điều này giúp hệ thống chặn phương án chưa đủ an toàn trước khi đi xa hơn. "
            "Cách này vẫn có giá trị vì nó bảo vệ người dùng khỏi một phương án chưa chắc chắn."
        )

    return None
