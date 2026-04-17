"""Approval gate policy rules for lifecycle and approval workflows."""

from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import RiskLevel


@dataclass(frozen=True, slots=True)
class ApprovalGatePolicy:
    """Resolved policy decision for one risk level."""

    risk_level: RiskLevel | None
    risk_classification: str
    requires_human_approval: bool
    reason: str


def classify_risk_level(risk_level: RiskLevel | None) -> str:
    """Map a risk level into a coarse lifecycle class."""
    if risk_level in {RiskLevel.CRITICAL, RiskLevel.DANGER}:
        return "high"
    if risk_level is RiskLevel.WARNING:
        return "moderate"
    if risk_level is RiskLevel.SAFE:
        return "low"
    return "unknown"


def resolve_approval_gate_policy(risk_level: RiskLevel | None) -> ApprovalGatePolicy:
    """Resolve HITL gating policy from risk level."""
    risk_classification = classify_risk_level(risk_level)
    requires_human_approval = risk_level in {RiskLevel.DANGER, RiskLevel.CRITICAL}
    if risk_level is None:
        requires_human_approval = True

    if requires_human_approval:
        reason = "High or unknown risk requires human approval before execution."
    else:
        reason = "Risk is below high threshold and may be auto-approved by workflow policy."

    return ApprovalGatePolicy(
        risk_level=risk_level,
        risk_classification=risk_classification,
        requires_human_approval=requires_human_approval,
        reason=reason,
    )
