"""Policy guard for generated action plans."""

from __future__ import annotations

from app.models.enums import ActionType, RiskLevel
from app.schemas.agent import GeneratedActionPlan, PlanValidationResult

POLICY_VERSION = "v1"
CRITICAL_MITIGATION_ACTIONS = {
    ActionType.CLOSE_GATE,
    ActionType.START_PUMP,
    ActionType.STOP_PUMP,
    ActionType.CLOSE_GATE_SIMULATED,
    ActionType.START_PUMP_SIMULATED,
}


def validate_generated_plan(
    plan: GeneratedActionPlan,
    *,
    risk_level: RiskLevel,
) -> PlanValidationResult:
    """Validate a generated plan against MVP execution policy."""
    errors: list[str] = []
    warnings: list[str] = []

    expected_indexes = list(range(1, len(plan.steps) + 1))
    actual_indexes = [step.step_index for step in plan.steps]
    if actual_indexes != expected_indexes:
        errors.append("Plan step_index values must be sequential starting from 1.")

    if not plan.steps:
        errors.append("Plan must contain at least one step.")

    action_types = {step.action_type for step in plan.steps}
    for step in plan.steps:
        if not step.simulated:
            errors.append(
                f"Step {step.step_index} must remain simulated in MVP planning."
            )

    if risk_level in {RiskLevel.DANGER, RiskLevel.CRITICAL}:
        if not ({ActionType.NOTIFY_FARMERS, ActionType.SEND_ALERT} & action_types):
            warnings.append(
                "High-risk plan should notify farmers or local operators promptly."
            )

    if risk_level is RiskLevel.CRITICAL and not (
        action_types & CRITICAL_MITIGATION_ACTIONS
    ):
        errors.append(
            "Critical-risk plan must include a simulated hydraulic mitigation step."
        )

    return PlanValidationResult(
        is_valid=not errors,
        policy_version=POLICY_VERSION,
        errors=errors,
        warnings=warnings,
        normalized_steps=[
            step.model_dump(mode="json")
            for step in sorted(plan.steps, key=lambda item: item.step_index)
        ],
    )
