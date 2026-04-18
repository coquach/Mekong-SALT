"""Execution policy guard for simulated actions."""

from __future__ import annotations

from http import HTTPStatus

from app.agents.policy_guard import validate_generated_plan
from app.core.exceptions import AppException
from app.models.action import ActionPlan
from app.models.enums import ActionPlanStatus, RiskLevel
from app.schemas.agent import GeneratedActionPlan, PlanStep


def validate_execution_plan(plan: ActionPlan) -> list[PlanStep]:
    """Ensure a persisted plan is safe to execute in simulated mode."""
    if plan.status is not ActionPlanStatus.APPROVED:
        raise AppException(
            status_code=HTTPStatus.BAD_REQUEST,
            code="action_plan_not_approved",
            message="Only approved plans can be executed in simulated mode.",
        )
    if plan.risk_assessment is None:
        raise AppException(
            status_code=HTTPStatus.BAD_REQUEST,
            code="action_plan_missing_assessment",
            message="Action plan is missing its linked risk assessment.",
        )

    try:
        steps = [PlanStep.model_validate(step) for step in plan.plan_steps]
        generated_plan = GeneratedActionPlan(
            objective=plan.objective,
            summary=plan.summary,
            assumptions=list((plan.assumptions or {}).get("items", [])),
            steps=steps,
        )
    except Exception as exc:
        raise AppException(
            status_code=HTTPStatus.BAD_REQUEST,
            code="action_plan_invalid_structure",
            message="Action plan payload is not structurally valid for execution.",
        ) from exc

    validation_result = validate_generated_plan(
        generated_plan,
        risk_level=plan.risk_assessment.risk_level,
    )
    if not validation_result.is_valid:
        raise AppException(
            status_code=HTTPStatus.BAD_REQUEST,
            code="action_plan_policy_violation",
            message="Action plan failed execution policy validation.",
            details=validation_result.model_dump(mode="json"),
        )
    return steps


def is_auto_execution_eligible(
    plan: ActionPlan,
    *,
    risk_level: RiskLevel | None,
) -> tuple[bool, str]:
    """Return whether an approved plan can proceed to simulated execution."""
    if risk_level is None:
        return (
            False,
            "Risk level is missing; execution requires an approved plan with risk context.",
        )

    try:
        _ = [PlanStep.model_validate(step) for step in plan.plan_steps]
    except Exception:
        return (
            False,
            "Plan steps are not structurally valid for auto-execution eligibility checks.",
        )
    return True, "Plan is eligible for simulated execution after approval."
