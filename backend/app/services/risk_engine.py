"""Pure deterministic salinity risk evaluation logic."""

from dataclasses import dataclass
from decimal import Decimal

from app.models.enums import RiskLevel, TrendDirection

SALINITY_SAFE_THRESHOLD = Decimal("1.00")
SALINITY_WARNING_THRESHOLD = Decimal("2.50")
SALINITY_DANGER_THRESHOLD = Decimal("4.00")
TREND_ESCALATION_THRESHOLD = Decimal("0.50")
TREND_DEESCALATION_THRESHOLD = Decimal("-0.50")
TREND_RISING_THRESHOLD = Decimal("0.30")
TREND_FALLING_THRESHOLD = Decimal("-0.30")
EXTERNAL_WIND_THRESHOLD = Decimal("5.00")
EXTERNAL_TIDE_THRESHOLD = Decimal("1.50")
MAX_EXTERNAL_SCORE_DELTA = 1

RISK_SCORES = {
    RiskLevel.SAFE: 0,
    RiskLevel.WARNING: 1,
    RiskLevel.DANGER: 2,
    RiskLevel.CRITICAL: 3,
}

SCORE_TO_RISK = {score: level for level, score in RISK_SCORES.items()}


@dataclass(slots=True)
class RiskEvaluationInput:
    """Normalized factors used by the deterministic engine."""

    salinity_dsm: Decimal
    previous_salinity_dsm: Decimal | None
    wind_speed_mps: Decimal | None
    tide_level_m: Decimal | None


@dataclass(slots=True)
class RiskEvaluationOutput:
    """Deterministic engine output before persistence."""

    risk_level: RiskLevel
    trend_direction: TrendDirection
    trend_delta_dsm: Decimal | None
    summary: str
    rationale: dict[str, object]


def evaluate_risk(inputs: RiskEvaluationInput) -> RiskEvaluationOutput:
    """Evaluate current risk using a sensor-first policy.

    Local salinity and its trend are the primary decision signals. External wind and
    tide are only allowed to modify an already elevated sensor-derived risk and may
    not independently turn a safe local reading into an alerting state.
    """
    base_level = _base_level_from_salinity(inputs.salinity_dsm)
    trend_direction, trend_delta = _trend_from_history(
        inputs.salinity_dsm, inputs.previous_salinity_dsm
    )

    score = RISK_SCORES[base_level]
    adjustments: list[str] = []

    if (
        trend_direction is TrendDirection.RISING
        and trend_delta is not None
        and trend_delta >= TREND_ESCALATION_THRESHOLD
    ):
        score += 1
        adjustments.append("rising salinity trend escalated the base risk by one level")
    elif (
        trend_direction is TrendDirection.FALLING
        and trend_delta is not None
        and trend_delta <= TREND_DEESCALATION_THRESHOLD
    ):
        score -= 1
        adjustments.append("falling salinity trend reduced the base risk by one level")

    sensor_score = min(max(score, 0), max(SCORE_TO_RISK))
    external_modifier_applied = False
    if (
        inputs.wind_speed_mps is not None
        and inputs.tide_level_m is not None
        and inputs.wind_speed_mps >= EXTERNAL_WIND_THRESHOLD
        and inputs.tide_level_m >= EXTERNAL_TIDE_THRESHOLD
    ):
        if sensor_score >= RISK_SCORES[RiskLevel.WARNING]:
            score += MAX_EXTERNAL_SCORE_DELTA
            external_modifier_applied = True
            adjustments.append(
                "strong wind plus elevated tide increased intrusion pressure"
            )
        else:
            adjustments.append(
                "strong wind and tide were observed but did not override a safe local reading"
            )

    bounded_score = min(max(score, 0), max(SCORE_TO_RISK))
    final_level = SCORE_TO_RISK[bounded_score]

    summary = (
        f"Risk assessed as {final_level.value} from salinity {inputs.salinity_dsm} dS/m"
        f" with trend {trend_direction.value}."
    )
    rationale = {
        "base_level": base_level.value,
        "salinity_dsm": str(inputs.salinity_dsm),
        "previous_salinity_dsm": (
            str(inputs.previous_salinity_dsm)
            if inputs.previous_salinity_dsm is not None
            else None
        ),
        "trend_direction": trend_direction.value,
        "trend_delta_dsm": str(trend_delta) if trend_delta is not None else None,
        "wind_speed_mps": (
            str(inputs.wind_speed_mps) if inputs.wind_speed_mps is not None else None
        ),
        "tide_level_m": str(inputs.tide_level_m) if inputs.tide_level_m is not None else None,
        "policy": {
            "sensor_is_primary": True,
            "external_context_is_modifier_only": True,
            "max_external_score_delta": MAX_EXTERNAL_SCORE_DELTA,
            "external_modifier_applied": external_modifier_applied,
        },
        "adjustments": adjustments,
    }

    return RiskEvaluationOutput(
        risk_level=final_level,
        trend_direction=trend_direction,
        trend_delta_dsm=trend_delta,
        summary=summary,
        rationale=rationale,
    )


def should_create_alert(risk_level: RiskLevel) -> bool:
    """Return whether the system should create an alert for this risk level."""
    return risk_level in {RiskLevel.DANGER, RiskLevel.CRITICAL}


def _base_level_from_salinity(salinity_dsm: Decimal) -> RiskLevel:
    if salinity_dsm < SALINITY_SAFE_THRESHOLD:
        return RiskLevel.SAFE
    if salinity_dsm < SALINITY_WARNING_THRESHOLD:
        return RiskLevel.WARNING
    if salinity_dsm < SALINITY_DANGER_THRESHOLD:
        return RiskLevel.DANGER
    return RiskLevel.CRITICAL


def _trend_from_history(
    current_salinity: Decimal, previous_salinity: Decimal | None
) -> tuple[TrendDirection, Decimal | None]:
    if previous_salinity is None:
        return TrendDirection.UNKNOWN, None

    delta = current_salinity - previous_salinity
    if delta >= TREND_RISING_THRESHOLD:
        return TrendDirection.RISING, delta
    if delta <= TREND_FALLING_THRESHOLD:
        return TrendDirection.FALLING, delta
    return TrendDirection.STABLE, delta
