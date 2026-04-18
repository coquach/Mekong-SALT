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


def test_evaluate_risk_uses_trend_window_for_consistent_rising_momentum():
    result = evaluate_risk(
        RiskEvaluationInput(
            salinity_dsm=Decimal("3.40"),
            previous_salinity_dsm=Decimal("2.90"),
            trend_window_salinity_dsm=[
                Decimal("2.40"),
                Decimal("2.90"),
                Decimal("3.40"),
            ],
            wind_speed_mps=None,
            tide_level_m=None,
            previous_reading_gap_minutes=Decimal("10"),
            reading_age_minutes=Decimal("6"),
            battery_level_pct=Decimal("75.00"),
        )
    )

    assert result.risk_level is RiskLevel.CRITICAL
    assert result.trend_direction is TrendDirection.RISING
    assert result.trend_delta_dsm == Decimal("1.00")
    assert any(
        "trend_window=" in item
        for item in result.rationale["trend_window_salinity_dsm"]
    )


def test_evaluate_risk_keeps_current_salinity_band_when_trend_is_falling():
    result = evaluate_risk(
        RiskEvaluationInput(
            salinity_dsm=Decimal("2.20"),
            previous_salinity_dsm=Decimal("2.90"),
            wind_speed_mps=Decimal("2.00"),
            tide_level_m=Decimal("0.80"),
        )
    )

    assert result.risk_level is RiskLevel.WARNING
    assert result.trend_direction is TrendDirection.FALLING
    assert result.trend_delta_dsm == Decimal("-0.70")
    assert result.rationale["policy"]["salinity_band_is_floor"] is True


def test_evaluate_risk_treats_noisy_trend_window_as_stable():
    result = evaluate_risk(
        RiskEvaluationInput(
            salinity_dsm=Decimal("3.00"),
            previous_salinity_dsm=Decimal("2.60"),
            trend_window_salinity_dsm=[
                Decimal("3.00"),
                Decimal("2.60"),
                Decimal("3.00"),
            ],
            wind_speed_mps=None,
            tide_level_m=None,
            previous_reading_gap_minutes=Decimal("8"),
            reading_age_minutes=Decimal("5"),
            battery_level_pct=Decimal("78.00"),
        )
    )

    assert result.risk_level is RiskLevel.DANGER
    assert result.trend_direction is TrendDirection.STABLE
    assert result.trend_delta_dsm == Decimal("0.00")
    assert any(
        "trend_window=" in item
        for item in result.rationale["trend_window_salinity_dsm"]
    )


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


def test_stale_history_prevents_trend_escalation():
    result = evaluate_risk(
        RiskEvaluationInput(
            salinity_dsm=Decimal("3.40"),
            previous_salinity_dsm=Decimal("2.20"),
            wind_speed_mps=None,
            tide_level_m=None,
            previous_reading_gap_minutes=Decimal("180"),
            reading_age_minutes=Decimal("5"),
            battery_level_pct=Decimal("82.00"),
        )
    )

    assert result.risk_level is RiskLevel.DANGER
    assert result.confidence_level == "high"
    assert result.rationale["policy"]["trend_requires_recent_history"] is True


def test_stale_low_battery_reading_is_marked_low_confidence():
    result = evaluate_risk(
        RiskEvaluationInput(
            salinity_dsm=Decimal("4.10"),
            previous_salinity_dsm=None,
            wind_speed_mps=None,
            tide_level_m=None,
            reading_age_minutes=Decimal("90"),
            battery_level_pct=Decimal("15.00"),
        )
    )

    assert result.risk_level is RiskLevel.CRITICAL
    assert result.confidence_level == "low"
    assert result.rationale["confidence"]["level"] == "low"


def test_hysteresis_holds_previous_warning_band_near_safe_boundary():
    result = evaluate_risk(
        RiskEvaluationInput(
            salinity_dsm=Decimal("0.95"),
            previous_salinity_dsm=Decimal("1.08"),
            wind_speed_mps=None,
            tide_level_m=None,
            previous_reading_gap_minutes=Decimal("5"),
            reading_age_minutes=Decimal("4"),
            battery_level_pct=Decimal("80.00"),
        )
    )

    assert result.risk_level is RiskLevel.WARNING
    assert result.rationale["policy"]["hysteresis_enabled"] is True
    assert any("hysteresis held risk" in item for item in result.rationale["adjustments"])


def test_hysteresis_releases_when_salinity_drops_below_exit_threshold():
    result = evaluate_risk(
        RiskEvaluationInput(
            salinity_dsm=Decimal("0.85"),
            previous_salinity_dsm=Decimal("1.08"),
            wind_speed_mps=None,
            tide_level_m=None,
            previous_reading_gap_minutes=Decimal("5"),
            reading_age_minutes=Decimal("4"),
            battery_level_pct=Decimal("80.00"),
        )
    )

    assert result.risk_level is RiskLevel.SAFE
