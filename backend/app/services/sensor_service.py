"""Sensor ingestion and query services."""

from http import HTTPStatus
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.enums import StationStatus
from app.models.sensor import SensorReading
from app.repositories.region import RegionRepository
from app.repositories.sensor import SensorReadingRepository, SensorStationRepository
from app.schemas.sensor import SensorReadingHistoryFilters, SensorReadingIngestRequest

logger = logging.getLogger(__name__)


async def ingest_sensor_reading(
    session: AsyncSession, payload: SensorReadingIngestRequest
) -> SensorReading:
    """Validate and persist a sensor reading."""
    station_repo = SensorStationRepository(session)
    reading_repo = SensorReadingRepository(session)

    station = await station_repo.get_by_code(payload.station_code)
    if station is None:
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="sensor_station_not_found",
            message=f"Sensor station '{payload.station_code}' was not found.",
        )
    if station.status is not StationStatus.ACTIVE:
        raise AppException(
            status_code=HTTPStatus.CONFLICT,
            code="sensor_station_inactive",
            message=f"Sensor station '{payload.station_code}' is not active.",
        )

    reading = SensorReading(
        station_id=station.id,
        recorded_at=payload.recorded_at,
        salinity_dsm=payload.salinity_dsm,
        water_level_m=payload.water_level_m,
        temperature_c=payload.temperature_c,
        battery_level_pct=payload.battery_level_pct,
        context_payload=payload.context_payload,
    )
    await reading_repo.add(reading)
    await session.commit()

    created = await reading_repo.get_with_station(reading.id)
    logger.info("Persisted sensor reading for station %s", payload.station_code)
    if created is None:
        raise AppException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            code="sensor_reading_reload_failed",
            message="Reading was stored but could not be reloaded.",
        )
    return created


async def list_latest_sensor_readings(
    session: AsyncSession, filters: SensorReadingHistoryFilters
) -> list[SensorReading]:
    """Return latest readings under station/region filters."""
    station_id, region_id = await _resolve_filter_ids(session, filters)
    reading_repo = SensorReadingRepository(session)
    return list(
        await reading_repo.list_latest(
            station_id=station_id,
            region_id=region_id,
            start_at=filters.start_at,
            end_at=filters.end_at,
            limit=filters.limit,
        )
    )


async def list_sensor_reading_history(
    session: AsyncSession, filters: SensorReadingHistoryFilters
) -> list[SensorReading]:
    """Return filtered reading history."""
    station_id, region_id = await _resolve_filter_ids(session, filters)
    reading_repo = SensorReadingRepository(session)
    return list(
        await reading_repo.list_history(
            station_id=station_id,
            region_id=region_id,
            start_at=filters.start_at,
            end_at=filters.end_at,
            limit=filters.limit,
        )
    )


async def _resolve_filter_ids(
    session: AsyncSession, filters: SensorReadingHistoryFilters
) -> tuple[UUID | None, UUID | None]:
    """Resolve station and region codes to UUIDs with basic validation."""
    if filters.start_at and filters.end_at and filters.start_at > filters.end_at:
        raise AppException(
            status_code=HTTPStatus.BAD_REQUEST,
            code="invalid_time_range",
            message="start_at must be earlier than or equal to end_at.",
        )

    station_repo = SensorStationRepository(session)
    region_repo = RegionRepository(session)

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

    return (
        station.id if station is not None else filters.station_id,
        region.id if region is not None else filters.region_id,
    )
