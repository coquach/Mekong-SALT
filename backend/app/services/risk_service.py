"""Risk assessment orchestration and alert evaluation services."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from http import HTTPStatus

from sqlalchemy.ext.asyncio import AsyncSession

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
from app.services.risk_engine import RiskEvaluationInput, evaluate_risk, should_create_alert


@dataclass(slots=True)
class RiskEvaluationBundle:
    """Aggregated result returned from current risk evaluation."""

    assessment: RiskAssessment
    reading: SensorReading
    weather_snapshot: WeatherSnapshot | None


@dataclass(slots=True)
class AlertEvaluationBundle:
    """Aggregated result returned from alert evaluation."""

    assessment: RiskAssessment
    reading: SensorReading
    weather_snapshot: WeatherSnapshot | None
    alert: AlertEvent | None
    alert_created: bool


async def evaluate_current_risk(
    session: AsyncSession,
    *,
    filters: RiskEvaluationFilters,
    redis_manager: RedisManager | None,
) -> RiskEvaluationBundle:
    """Evaluate and persist the current deterministic risk for a target reading."""
    region_repo = RegionRepository(session)
    reading_repo = SensorReadingRepository(session)

    reading = await _resolve_target_reading(session, filters)
    region = await region_repo.get(reading.station.region_id)
    if region is None:
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="region_not_found",
            message=f"Region '{reading.station.region_id}' was not found.",
        )

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
    await session.commit()
    await session.refresh(assessment)

    return RiskEvaluationBundle(
        assessment=assessment,
        reading=reading,
        weather_snapshot=weather_snapshot,
    )


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
    )
    if not should_create_alert(risk_bundle.assessment.risk_level):
        return AlertEvaluationBundle(
            assessment=risk_bundle.assessment,
            reading=risk_bundle.reading,
            weather_snapshot=risk_bundle.weather_snapshot,
            alert=None,
            alert_created=False,
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
    )


async def _resolve_target_reading(
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
        f"wind={wind_context}, tide={tide_context}."
    )
