"""Pure deterministic salinity risk evaluation logic."""

from dataclasses import dataclass
from decimal import Decimal
from collections.abc import Sequence

from app.core.salinity_units import (
    SALINITY_DANGER_THRESHOLD_DSM,
    SALINITY_SAFE_THRESHOLD_DSM,
    SALINITY_WARNING_THRESHOLD_DSM,
    dsm_to_gl,
)
from app.models.enums import RiskLevel, TrendDirection

TREND_ESCALATION_THRESHOLD = Decimal("0.50")
TREND_DEESCALATION_THRESHOLD = Decimal("-0.50")
TREND_RISING_THRESHOLD = Decimal("0.30")
TREND_FALLING_THRESHOLD = Decimal("-0.30")
EXTERNAL_WIND_THRESHOLD = Decimal("5.00")
EXTERNAL_TIDE_THRESHOLD = Decimal("1.50")
MAX_TREND_HISTORY_GAP_MINUTES = Decimal("60")
MAX_READING_AGE_FOR_EXTERNAL_CONTEXT_MINUTES = Decimal("45")
MAX_EXTERNAL_SCORE_DELTA = 1
HYSTERESIS_EXIT_THRESHOLDS = {
    RiskLevel.WARNING: Decimal("0.90"),
    RiskLevel.DANGER: Decimal("2.35"),
    RiskLevel.CRITICAL: Decimal("3.85"),
}

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
    trend_window_salinity_dsm: Sequence[Decimal] | None = None
    previous_reading_gap_minutes: Decimal | None = None
    reading_age_minutes: Decimal | None = None
    battery_level_pct: Decimal | None = None


@dataclass(slots=True)
class RiskEvaluationOutput:
    """Deterministic engine output before persistence."""

    risk_level: RiskLevel
    trend_direction: TrendDirection
    trend_delta_dsm: Decimal | None
    confidence_level: str
    confidence_score: Decimal
    summary: str
    rationale: dict[str, object]


def evaluate_risk(inputs: RiskEvaluationInput) -> RiskEvaluationOutput:
    """Evaluate current risk using a sensor-first policy.

    Local salinity and its trend are the primary decision signals. External wind and
    tide are only allowed to modify an already elevated sensor-derived risk and may
    not independently turn a safe local reading into an alerting state.
    """
    base_level = _base_level_from_salinity(inputs.salinity_dsm)
    base_score = RISK_SCORES[base_level]
    trend_direction, trend_delta, trend_window = _trend_from_history(
        current_salinity=inputs.salinity_dsm,
        previous_salinity=inputs.previous_salinity_dsm,
        trend_window_salinity_dsm=inputs.trend_window_salinity_dsm,
    )
    trend_is_reliable = _is_trend_reliable(
        previous_reading_gap_minutes=inputs.previous_reading_gap_minutes,
        reading_age_minutes=inputs.reading_age_minutes,
    )
    external_context_is_fresh = _is_external_context_fresh(inputs.reading_age_minutes)

    score = base_score
    adjustments: list[str] = []
    hysteresis_level = _apply_hysteresis(
        current_level=base_level,
        current_salinity=inputs.salinity_dsm,
        previous_salinity=inputs.previous_salinity_dsm,
        trend_is_reliable=trend_is_reliable,
    )
    if hysteresis_level is not base_level:
        adjustments.append(
            f"hysteresis held risk at {hysteresis_level.value} until salinity crossed the exit threshold"
        )

    if (
        trend_direction is TrendDirection.RISING
        and trend_delta is not None
        and trend_delta >= TREND_ESCALATION_THRESHOLD
        and trend_is_reliable
    ):
        score += 1
        adjustments.append("rising salinity trend escalated the base risk by one level")
    elif (
        trend_direction is TrendDirection.FALLING
        and trend_delta is not None
        and trend_delta <= TREND_DEESCALATION_THRESHOLD
    ):
        adjustments.append(
            "falling salinity trend observed, but risk stays anchored to the current salinity band"
        )
        if not trend_is_reliable:
            adjustments.append(
                "trend history is too old to be used as a de-escalation signal"
            )

    sensor_score = min(max(score, 0), max(SCORE_TO_RISK))
    external_modifier_applied = False
    if (
        external_context_is_fresh
        and inputs.wind_speed_mps is not None
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
    elif (
        inputs.wind_speed_mps is not None
        and inputs.tide_level_m is not None
        and inputs.wind_speed_mps >= EXTERNAL_WIND_THRESHOLD
        and inputs.tide_level_m >= EXTERNAL_TIDE_THRESHOLD
    ):
        adjustments.append("external context ignored because the reading is too stale")

    bounded_score = min(max(score, 0), max(SCORE_TO_RISK))
    floor_score = max(RISK_SCORES[hysteresis_level], base_score)
    final_score = max(floor_score, bounded_score)
    final_level = SCORE_TO_RISK[final_score]
    confidence_score = _compute_confidence_score(
        previous_reading_gap_minutes=inputs.previous_reading_gap_minutes,
        wind_speed_mps=inputs.wind_speed_mps,
        tide_level_m=inputs.tide_level_m,
        reading_age_minutes=inputs.reading_age_minutes,
        battery_level_pct=inputs.battery_level_pct,
        has_previous_reading=inputs.previous_salinity_dsm is not None,
        has_external_context=inputs.wind_speed_mps is not None and inputs.tide_level_m is not None,
    )
    confidence_level = _confidence_level(confidence_score)
    salinity_gl = dsm_to_gl(inputs.salinity_dsm)
    previous_salinity_gl = dsm_to_gl(inputs.previous_salinity_dsm)
    trend_delta_gl = dsm_to_gl(trend_delta) if trend_delta is not None else None

    summary = (
        f"Risk assessed as {final_level.value} from salinity {inputs.salinity_dsm} dS/m"
        f" (~{salinity_gl} g/L)"
        f" with trend {trend_direction.value}"
        f" and confidence {confidence_level}."
    )
    rationale = {
        "base_level": base_level.value,
        "salinity_dsm": str(inputs.salinity_dsm),
        "salinity_gl": str(salinity_gl) if salinity_gl is not None else None,
        "previous_salinity_dsm": (
            str(inputs.previous_salinity_dsm)
            if inputs.previous_salinity_dsm is not None
            else None
        ),
        "previous_salinity_gl": (
            str(previous_salinity_gl) if previous_salinity_gl is not None else None
        ),
        "trend_direction": trend_direction.value,
        "trend_delta_dsm": str(trend_delta) if trend_delta is not None else None,
        "trend_delta_gl": str(trend_delta_gl) if trend_delta_gl is not None else None,
        "trend_window_salinity_dsm": trend_window,
        "previous_reading_gap_minutes": (
            str(inputs.previous_reading_gap_minutes)
            if inputs.previous_reading_gap_minutes is not None
            else None
        ),
        "wind_speed_mps": (
            str(inputs.wind_speed_mps) if inputs.wind_speed_mps is not None else None
        ),
        "tide_level_m": str(inputs.tide_level_m) if inputs.tide_level_m is not None else None,
        "reading_age_minutes": (
            str(inputs.reading_age_minutes) if inputs.reading_age_minutes is not None else None
        ),
        "battery_level_pct": (
            str(inputs.battery_level_pct) if inputs.battery_level_pct is not None else None
        ),
        "policy": {
            "sensor_is_primary": True,
            "external_context_is_modifier_only": True,
            "salinity_band_is_floor": True,
            "hysteresis_enabled": True,
            "trend_requires_recent_history": True,
            "external_context_requires_recent_reading": True,
            "max_external_score_delta": MAX_EXTERNAL_SCORE_DELTA,
            "external_modifier_applied": external_modifier_applied,
            "thresholds": {
                "safe_threshold_dsm": str(SALINITY_SAFE_THRESHOLD_DSM),
                "safe_threshold_gl": str(dsm_to_gl(SALINITY_SAFE_THRESHOLD_DSM)),
                "warning_threshold_dsm": str(SALINITY_WARNING_THRESHOLD_DSM),
                "warning_threshold_gl": str(dsm_to_gl(SALINITY_WARNING_THRESHOLD_DSM)),
                "danger_threshold_dsm": str(SALINITY_DANGER_THRESHOLD_DSM),
                "danger_threshold_gl": str(dsm_to_gl(SALINITY_DANGER_THRESHOLD_DSM)),
            },
        },
        "confidence": {
            "score": str(confidence_score),
            "level": confidence_level,
        },
        "adjustments": adjustments,
    }

    return RiskEvaluationOutput(
        risk_level=final_level,
        trend_direction=trend_direction,
        trend_delta_dsm=trend_delta,
        confidence_level=confidence_level,
        confidence_score=confidence_score,
        summary=summary,
        rationale=rationale,
    )


def should_create_alert(risk_level: RiskLevel) -> bool:
    """Return whether the system should create an alert for this risk level."""
    return risk_level in {RiskLevel.DANGER, RiskLevel.CRITICAL}


def _base_level_from_salinity(salinity_dsm: Decimal) -> RiskLevel:
    if salinity_dsm < SALINITY_SAFE_THRESHOLD_DSM:
        return RiskLevel.SAFE
    if salinity_dsm < SALINITY_WARNING_THRESHOLD_DSM:
        return RiskLevel.WARNING
    if salinity_dsm < SALINITY_DANGER_THRESHOLD_DSM:
        return RiskLevel.DANGER
    return RiskLevel.CRITICAL


def _trend_from_history(
    *,
    current_salinity: Decimal,
    previous_salinity: Decimal | None,
    trend_window_salinity_dsm: Sequence[Decimal] | None,
) -> tuple[TrendDirection, Decimal | None, list[str] | None]:
    if trend_window_salinity_dsm is not None:
        window = [value for value in trend_window_salinity_dsm]
        if len(window) >= 3:
            if window[-1] != current_salinity:
                window = [*window, current_salinity]
            return _trend_from_window(window)

    if previous_salinity is None:
        return TrendDirection.UNKNOWN, None, None

    delta = current_salinity - previous_salinity
    if delta >= TREND_RISING_THRESHOLD:
        return TrendDirection.RISING, delta, [f"trend_delta={delta}"]
    if delta <= TREND_FALLING_THRESHOLD:
        return TrendDirection.FALLING, delta, [f"trend_delta={delta}"]
    return TrendDirection.STABLE, delta, [f"trend_delta={delta}"]


def _trend_from_window(window: Sequence[Decimal]) -> tuple[TrendDirection, Decimal | None, list[str]]:
    values = list(window)
    if len(values) < 2:
        return TrendDirection.UNKNOWN, None, [f"trend_window={values}"]

    deltas = [right - left for left, right in zip(values, values[1:])]
    rising_votes = sum(1 for delta in deltas if delta >= TREND_RISING_THRESHOLD)
    falling_votes = sum(1 for delta in deltas if delta <= TREND_FALLING_THRESHOLD)
    net_delta = values[-1] - values[0]
    adjustments = [
        f"trend_window={values}",
        f"trend_window_deltas={deltas}",
        f"trend_window_net_delta={net_delta}",
    ]

    if rising_votes >= 2 and rising_votes > falling_votes:
        return TrendDirection.RISING, net_delta, adjustments
    if falling_votes >= 2 and falling_votes > rising_votes:
        return TrendDirection.FALLING, net_delta, adjustments
    if net_delta >= TREND_RISING_THRESHOLD:
        adjustments.append("trend_window classified as stable because momentum was not consistent enough to escalate")
        return TrendDirection.STABLE, net_delta, adjustments
    if net_delta <= TREND_FALLING_THRESHOLD:
        adjustments.append("trend_window classified as stable because momentum was not consistent enough to de-escalate")
        return TrendDirection.STABLE, net_delta, adjustments
    return TrendDirection.STABLE, net_delta, adjustments


def _is_trend_reliable(
    *,
    previous_reading_gap_minutes: Decimal | None,
    reading_age_minutes: Decimal | None,
) -> bool:
    if previous_reading_gap_minutes is not None and previous_reading_gap_minutes > MAX_TREND_HISTORY_GAP_MINUTES:
        return False
    if reading_age_minutes is not None and reading_age_minutes > MAX_TREND_HISTORY_GAP_MINUTES:
        return False
    return True


def _is_external_context_fresh(reading_age_minutes: Decimal | None) -> bool:
    if reading_age_minutes is None:
        return True
    return reading_age_minutes <= MAX_READING_AGE_FOR_EXTERNAL_CONTEXT_MINUTES


def _compute_confidence_score(
    *,
    previous_reading_gap_minutes: Decimal | None,
    wind_speed_mps: Decimal | None,
    tide_level_m: Decimal | None,
    reading_age_minutes: Decimal | None,
    battery_level_pct: Decimal | None,
    has_previous_reading: bool,
    has_external_context: bool,
) -> Decimal:
    score = Decimal("0.70")

    if has_previous_reading:
        score += Decimal("0.05")
    else:
        score -= Decimal("0.10")

    if has_external_context:
        score += Decimal("0.05")

    if reading_age_minutes is not None:
        if reading_age_minutes <= Decimal("15"):
            score += Decimal("0.10")
        elif reading_age_minutes <= Decimal("30"):
            score += Decimal("0.05")
        elif reading_age_minutes <= Decimal("60"):
            score -= Decimal("0.05")
        else:
            score -= Decimal("0.20")

    if previous_reading_gap_minutes is not None:
        if previous_reading_gap_minutes <= Decimal("30"):
            score += Decimal("0.05")
        elif previous_reading_gap_minutes > Decimal("120"):
            score -= Decimal("0.10")

    if battery_level_pct is not None:
        if battery_level_pct < Decimal("20"):
            score -= Decimal("0.15")
        elif battery_level_pct < Decimal("40"):
            score -= Decimal("0.05")
        else:
            score += Decimal("0.05")

    if wind_speed_mps is not None and tide_level_m is not None:
        score += Decimal("0.03")

    return min(max(score, Decimal("0.00")), Decimal("1.00"))


def _confidence_level(score: Decimal) -> str:
    if score >= Decimal("0.80"):
        return "high"
    if score >= Decimal("0.55"):
        return "medium"
    return "low"


def _apply_hysteresis(
    *,
    current_level: RiskLevel,
    current_salinity: Decimal,
    previous_salinity: Decimal | None,
    trend_is_reliable: bool,
) -> RiskLevel:
    """Keep risk sticky near exit thresholds to avoid band flapping."""
    if not trend_is_reliable or previous_salinity is None:
        return current_level

    previous_level = _base_level_from_salinity(previous_salinity)
    if RISK_SCORES[previous_level] <= RISK_SCORES[current_level]:
        return current_level

    exit_threshold = HYSTERESIS_EXIT_THRESHOLDS.get(previous_level)
    if exit_threshold is None:
        return current_level
    if current_salinity >= exit_threshold:
        return previous_level
    return current_level
