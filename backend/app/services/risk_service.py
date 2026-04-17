"""Risk assessment orchestration and alert evaluation services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from http import HTTPStatus
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.salinity_units import dsm_to_gl
from app.core.config import get_settings
from app.core.exceptions import AppException
from app.db.redis import RedisManager
from app.models.enums import AlertStatus
from app.models.risk import AlertEvent, RiskAssessment
from app.models.sensor import SensorReading
from app.models.weather import WeatherSnapshot
from app.repositories.region import RegionRepository
from app.repositories.risk import AlertEventRepository, RiskAssessmentRepository
from app.repositories.sensor import SensorReadingRepository, SensorStationRepository
from app.schemas.risk import RiskEvaluationFilters
from app.services.external_context_service import get_or_fetch_weather_snapshot
from app.services.incident_service import ensure_incident_for_assessment
from app.services.risk_engine import RiskEvaluationInput, evaluate_risk, should_create_alert
from app.services.agent_trace_service import (
    capture_observation_snapshot,
    finish_agent_run,
    start_agent_run,
)


@dataclass(slots=True)
class RiskEvaluationBundle:
    """Aggregated result returned from current risk evaluation."""

    assessment: RiskAssessment
    reading: SensorReading
    weather_snapshot: WeatherSnapshot | None
    run_id: UUID | None = None


@dataclass(slots=True)
class AlertEvaluationBundle:
    """Aggregated result returned from alert evaluation."""

    assessment: RiskAssessment
    reading: SensorReading
    weather_snapshot: WeatherSnapshot | None
    alert: AlertEvent | None
    alert_created: bool
    run_id: UUID | None = None


async def evaluate_current_risk(
    session: AsyncSession,
    *,
    filters: RiskEvaluationFilters,
    redis_manager: RedisManager | None,
    target_reading: SensorReading | None = None,
    trigger_source: str = "risk.current",
    trigger_payload: dict[str, Any] | None = None,
) -> RiskEvaluationBundle:
    """Evaluate and persist the current deterministic risk for a target reading."""
    region_repo = RegionRepository(session)
    reading_repo = SensorReadingRepository(session)

    reading = target_reading or await resolve_target_reading(session, filters)
    region = await region_repo.get(reading.station.region_id)
    if region is None:
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="region_not_found",
            message=f"Region '{reading.station.region_id}' was not found.",
        )

    run = await start_agent_run(
        session,
        run_type="risk_evaluation",
        trigger_source=trigger_source,
        payload={
            "filters": filters.model_dump(mode="json"),
            "trigger_payload": trigger_payload or {},
        },
        region_id=region.id,
        station_id=reading.station_id,
    )

    try:
        previous_reading = await reading_repo.get_previous_for_station(
            reading.station_id,
            before_recorded_at=reading.recorded_at,
            exclude_reading_id=reading.id,
        )
        weather_snapshot = await get_or_fetch_weather_snapshot(
            session,
            region=region,
            station=reading.station,
            redis_manager=redis_manager,
        )

        evaluation = evaluate_risk(
            RiskEvaluationInput(
                salinity_dsm=reading.salinity_dsm,
                previous_salinity_dsm=(
                    previous_reading.salinity_dsm if previous_reading is not None else None
                ),
                wind_speed_mps=(
                    weather_snapshot.wind_speed_mps if weather_snapshot is not None else None
                ),
                tide_level_m=(
                    weather_snapshot.tide_level_m if weather_snapshot is not None else None
                ),
            )
        )

        assessment = RiskAssessment(
            region_id=region.id,
            station_id=reading.station_id,
            based_on_reading_id=reading.id,
            based_on_weather_id=weather_snapshot.id if weather_snapshot is not None else None,
            assessed_at=datetime.now(UTC),
            risk_level=evaluation.risk_level,
            salinity_dsm=reading.salinity_dsm,
            trend_direction=evaluation.trend_direction,
            trend_delta_dsm=evaluation.trend_delta_dsm,
            rule_version=get_settings().risk_rule_version,
            summary=evaluation.summary,
            rationale=evaluation.rationale,
        )
        assessment_repo = RiskAssessmentRepository(session)
        await assessment_repo.add(assessment)

        await capture_observation_snapshot(
            session,
            run=run,
            source="risk.pre_incident_decision",
            payload={
                "reading": {
                    "id": str(reading.id),
                    "recorded_at": reading.recorded_at.isoformat(),
                    "salinity_dsm": str(reading.salinity_dsm),
                    "salinity_gl": (
                        str(dsm_to_gl(reading.salinity_dsm))
                        if reading.salinity_dsm is not None
                        else None
                    ),
                    "water_level_m": str(reading.water_level_m),
                },
                "previous_reading": (
                    {
                        "id": str(previous_reading.id),
                        "recorded_at": previous_reading.recorded_at.isoformat(),
                        "salinity_dsm": str(previous_reading.salinity_dsm),
                        "salinity_gl": (
                            str(dsm_to_gl(previous_reading.salinity_dsm))
                            if previous_reading.salinity_dsm is not None
                            else None
                        ),
                    }
                    if previous_reading is not None
                    else None
                ),
                "weather_snapshot": (
                    {
                        "id": str(weather_snapshot.id),
                        "observed_at": weather_snapshot.observed_at.isoformat(),
                        "wind_speed_mps": (
                            str(weather_snapshot.wind_speed_mps)
                            if weather_snapshot.wind_speed_mps is not None
                            else None
                        ),
                        "tide_level_m": (
                            str(weather_snapshot.tide_level_m)
                            if weather_snapshot.tide_level_m is not None
                            else None
                        ),
                    }
                    if weather_snapshot is not None
                    else None
                ),
                "evaluation": {
                    "risk_level": evaluation.risk_level.value,
                    "trend_direction": evaluation.trend_direction.value,
                    "trend_delta_dsm": (
                        str(evaluation.trend_delta_dsm)
                        if evaluation.trend_delta_dsm is not None
                        else None
                    ),
                    "trend_delta_gl": (
                        str(dsm_to_gl(evaluation.trend_delta_dsm))
                        if evaluation.trend_delta_dsm is not None
                        else None
                    ),
                    "summary": evaluation.summary,
                    "rationale": evaluation.rationale,
                },
            },
            region_id=region.id,
            station_id=reading.station_id,
            reading_id=reading.id,
            weather_snapshot_id=weather_snapshot.id if weather_snapshot is not None else None,
        )

        incident_decision = await ensure_incident_for_assessment(session, assessment)

        finish_agent_run(
            run,
            status="succeeded",
            trace={
                "incident_decision": {
                    "decision": incident_decision.decision,
                    "reason": incident_decision.reason,
                    "incident_id": (
                        str(incident_decision.incident.id)
                        if incident_decision.incident is not None
                        else None
                    ),
                },
                "plan_decision": {
                    "decision": "not_applicable",
                    "reason": "Risk evaluation run does not generate action plans.",
                },
                "assessment": {
                    "risk_assessment_id": str(assessment.id),
                    "risk_level": assessment.risk_level.value,
                },
            },
            risk_assessment_id=assessment.id,
            incident_id=(
                incident_decision.incident.id
                if incident_decision.incident is not None
                else None
            ),
        )

        await session.commit()
        await session.refresh(assessment)

        return RiskEvaluationBundle(
            assessment=assessment,
            reading=reading,
            weather_snapshot=weather_snapshot,
            run_id=run.id,
        )
    except Exception as exc:
        finish_agent_run(
            run,
            status="failed",
            trace={
                "incident_decision": {
                    "decision": "not_decided",
                    "reason": str(exc),
                },
                "plan_decision": {
                    "decision": "not_applicable",
                    "reason": "Risk evaluation run does not generate action plans.",
                },
            },
            error_message=str(exc),
        )
        await session.commit()
        raise


async def evaluate_alerts(
    session: AsyncSession,
    *,
    filters: RiskEvaluationFilters,
    redis_manager: RedisManager | None,
) -> AlertEvaluationBundle:
    """Evaluate current risk and create an alert when the rules require it."""
    risk_bundle = await evaluate_current_risk(
        session,
        filters=filters,
        redis_manager=redis_manager,
        trigger_source="alerts.evaluate",
        trigger_payload={"mode": "alert_evaluation"},
    )
    if not should_create_alert(risk_bundle.assessment.risk_level):
        return AlertEvaluationBundle(
            assessment=risk_bundle.assessment,
            reading=risk_bundle.reading,
            weather_snapshot=risk_bundle.weather_snapshot,
            alert=None,
            alert_created=False,
            run_id=risk_bundle.run_id,
        )

    alert_repo = AlertEventRepository(session)
    existing_alert = await alert_repo.get_open_by_region_and_severity(
        risk_bundle.assessment.region_id,
        risk_bundle.assessment.risk_level,
    )
    if existing_alert is not None:
        return AlertEvaluationBundle(
            assessment=risk_bundle.assessment,
            reading=risk_bundle.reading,
            weather_snapshot=risk_bundle.weather_snapshot,
            alert=existing_alert,
            alert_created=False,
            run_id=risk_bundle.run_id,
        )

    alert = AlertEvent(
        region_id=risk_bundle.assessment.region_id,
        risk_assessment_id=risk_bundle.assessment.id,
        triggered_at=datetime.now(UTC),
        severity=risk_bundle.assessment.risk_level,
        title=_build_alert_title(risk_bundle),
        message=_build_alert_message(risk_bundle),
        status=AlertStatus.OPEN,
    )
    await alert_repo.add(alert)
    await session.commit()
    await session.refresh(alert)

    return AlertEvaluationBundle(
        assessment=risk_bundle.assessment,
        reading=risk_bundle.reading,
        weather_snapshot=risk_bundle.weather_snapshot,
        alert=alert,
        alert_created=True,
        run_id=risk_bundle.run_id,
    )


async def resolve_target_reading(
    session: AsyncSession,
    filters: RiskEvaluationFilters,
) -> SensorReading:
    """Select the latest relevant reading for risk evaluation."""
    station_repo = SensorStationRepository(session)
    region_repo = RegionRepository(session)
    reading_repo = SensorReadingRepository(session)

    station = None
    region = None

    if filters.station_code:
        station = await station_repo.get_by_code(filters.station_code)
        if station is None:
            raise AppException(
                status_code=HTTPStatus.NOT_FOUND,
                code="sensor_station_not_found",
                message=f"Sensor station '{filters.station_code}' was not found.",
            )
    elif filters.station_id:
        station = await station_repo.get(filters.station_id)
        if station is None:
            raise AppException(
                status_code=HTTPStatus.NOT_FOUND,
                code="sensor_station_not_found",
                message=f"Sensor station '{filters.station_id}' was not found.",
            )

    if filters.region_code:
        region = await region_repo.get_by_code(filters.region_code)
        if region is None:
            raise AppException(
                status_code=HTTPStatus.NOT_FOUND,
                code="region_not_found",
                message=f"Region '{filters.region_code}' was not found.",
            )
    elif filters.region_id:
        region = await region_repo.get(filters.region_id)
        if region is None:
            raise AppException(
                status_code=HTTPStatus.NOT_FOUND,
                code="region_not_found",
                message=f"Region '{filters.region_id}' was not found.",
            )

    if station is not None and region is not None and station.region_id != region.id:
        raise AppException(
            status_code=HTTPStatus.BAD_REQUEST,
            code="station_region_mismatch",
            message="station and region filters do not refer to the same region.",
        )

    if station is not None:
        reading = await reading_repo.get_latest_for_station(station.id)
        if reading is None:
            raise AppException(
                status_code=HTTPStatus.NOT_FOUND,
                code="sensor_reading_not_found",
                message=f"No readings were found for station '{station.code}'.",
            )
        return reading

    candidate_readings = list(
        await reading_repo.list_latest(region_id=region.id if region is not None else None)
    )
    if not candidate_readings:
        scope = f"region '{region.code}'" if region is not None else "the current filters"
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="sensor_reading_not_found",
            message=f"No readings were found for {scope}.",
        )

    candidate_readings.sort(
        key=lambda item: (
            Decimal(item.salinity_dsm),
            item.recorded_at,
            item.created_at,
        ),
        reverse=True,
    )
    return candidate_readings[0]


async def _resolve_target_reading(
    session: AsyncSession,
    filters: RiskEvaluationFilters,
) -> SensorReading:
    """Backward-compatible alias for internal callers."""
    return await resolve_target_reading(session, filters)


def _build_alert_title(bundle: RiskEvaluationBundle) -> str:
    """Build a compact alert title from the risk bundle."""
    station_code = bundle.reading.station.code
    return f"{bundle.assessment.risk_level.value.title()} salinity risk at {station_code}"


def _build_alert_message(bundle: RiskEvaluationBundle) -> str:
    """Build the alert body persisted with the alert event."""
    wind_context = "unknown"
    tide_context = "unknown"
    if bundle.weather_snapshot is not None:
        if bundle.weather_snapshot.wind_speed_mps is not None:
            wind_context = f"{bundle.weather_snapshot.wind_speed_mps} m/s"
        if bundle.weather_snapshot.tide_level_m is not None:
            tide_context = f"{bundle.weather_snapshot.tide_level_m} m"
    return (
        f"{bundle.assessment.summary} "
        f"Station={bundle.reading.station.code}, "
        f"salinity={bundle.reading.salinity_dsm} dS/m"
        f"/~{dsm_to_gl(bundle.reading.salinity_dsm)} g/L, "
        f"wind={wind_context}, tide={tide_context}."
    )
