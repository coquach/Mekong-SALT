"""Unit tests for approval gate policy extraction."""

from app.models.enums import RiskLevel
from app.services.approval.policy import classify_risk_level, resolve_approval_gate_policy


def test_classify_risk_level_mapping():
    assert classify_risk_level(RiskLevel.CRITICAL) == "high"
    assert classify_risk_level(RiskLevel.DANGER) == "high"
    assert classify_risk_level(RiskLevel.WARNING) == "moderate"
    assert classify_risk_level(RiskLevel.SAFE) == "low"
    assert classify_risk_level(None) == "unknown"


def test_approval_gate_policy_requires_human_for_high_and_unknown_risk():
    high_policy = resolve_approval_gate_policy(RiskLevel.DANGER)
    assert high_policy.risk_classification == "high"
    assert high_policy.requires_human_approval is True

    unknown_policy = resolve_approval_gate_policy(None)
    assert unknown_policy.risk_classification == "unknown"
    assert unknown_policy.requires_human_approval is True


def test_approval_gate_policy_allows_auto_approval_for_warning():
    policy = resolve_approval_gate_policy(RiskLevel.WARNING)
    assert policy.risk_classification == "moderate"
    assert policy.requires_human_approval is False
