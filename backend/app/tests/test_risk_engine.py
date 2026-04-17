"""Unit tests for the deterministic risk engine."""

from decimal import Decimal

from app.models.enums import RiskLevel, TrendDirection
from app.services.risk_engine import (
    RiskEvaluationInput,
    evaluate_risk,
    should_create_alert,
)


def test_evaluate_risk_escalates_with_rising_trend_and_external_pressure():
    result = evaluate_risk(
        RiskEvaluationInput(
            salinity_dsm=Decimal("3.40"),
            previous_salinity_dsm=Decimal("2.20"),
            wind_speed_mps=Decimal("5.50"),
            tide_level_m=Decimal("1.70"),
        )
    )

    assert result.risk_level is RiskLevel.CRITICAL
    assert result.trend_direction is TrendDirection.RISING
    assert result.trend_delta_dsm == Decimal("1.20")
    assert len(result.rationale["adjustments"]) == 2


def test_evaluate_risk_can_reduce_level_when_salinity_is_falling():
    result = evaluate_risk(
        RiskEvaluationInput(
            salinity_dsm=Decimal("2.20"),
            previous_salinity_dsm=Decimal("2.90"),
            wind_speed_mps=Decimal("2.00"),
            tide_level_m=Decimal("0.80"),
        )
    )

    assert result.risk_level is RiskLevel.SAFE
    assert result.trend_direction is TrendDirection.FALLING
    assert result.trend_delta_dsm == Decimal("-0.70")


def test_should_create_alert_only_for_danger_and_critical():
    assert should_create_alert(RiskLevel.SAFE) is False
    assert should_create_alert(RiskLevel.WARNING) is False
    assert should_create_alert(RiskLevel.DANGER) is True
    assert should_create_alert(RiskLevel.CRITICAL) is True


def test_external_context_does_not_override_safe_local_sensor_reading():
    result = evaluate_risk(
        RiskEvaluationInput(
            salinity_dsm=Decimal("0.80"),
            previous_salinity_dsm=Decimal("0.75"),
            wind_speed_mps=Decimal("6.20"),
            tide_level_m=Decimal("1.80"),
        )
    )

    assert result.risk_level is RiskLevel.SAFE
    assert result.trend_direction is TrendDirection.STABLE
    assert result.rationale["policy"]["sensor_is_primary"] is True
    assert result.rationale["policy"]["external_context_is_modifier_only"] is True
    assert result.rationale["policy"]["external_modifier_applied"] is False
