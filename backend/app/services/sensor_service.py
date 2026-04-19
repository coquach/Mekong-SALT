"""Sensor ingestion and query services."""

from http import HTTPStatus
import logging
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.enums import StationStatus
from app.models.sensor import SensorReading, SensorStation
from app.repositories.region import RegionRepository
from app.repositories.sensor import SensorReadingRepository, SensorStationRepository
from app.schemas.sensor import (
    SensorReadingHistoryFilters,
    SensorReadingIngestRequest,
    SensorStationCreate,
    SensorStationUpdate,
)

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
    if payload.salinity_dsm is None:
        raise AppException(
            status_code=HTTPStatus.BAD_REQUEST,
            code="invalid_sensor_salinity",
            message="salinity_dsm could not be resolved from input payload.",
        )

    existing = await reading_repo.get_by_station_recorded_source(
        station_id=station.id,
        recorded_at=payload.recorded_at,
        source=payload.source,
    )
    if existing is not None:
        logger.info(
            "Skipped duplicate sensor reading for station %s (recorded_at=%s source=%s)",
            payload.station_code,
            payload.recorded_at.isoformat(),
            payload.source,
        )
        return existing

    reading = SensorReading(
        station_id=station.id,
        recorded_at=payload.recorded_at,
        salinity_dsm=payload.salinity_dsm,
        water_level_m=payload.water_level_m,
        wind_speed_mps=payload.wind_speed_mps,
        wind_direction_deg=payload.wind_direction_deg,
        flow_rate_m3s=payload.flow_rate_m3s,
        temperature_c=payload.temperature_c,
        battery_level_pct=payload.battery_level_pct,
        source=payload.source,
        context_payload=payload.context_payload,
    )
    try:
        await reading_repo.add(reading)
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        if _is_duplicate_ingest_conflict(exc):
            duplicate = await reading_repo.get_by_station_recorded_source(
                station_id=station.id,
                recorded_at=payload.recorded_at,
                source=payload.source,
            )
            if duplicate is not None:
                logger.info(
                    "Resolved duplicate sensor reading via unique constraint for station %s "
                    "(recorded_at=%s source=%s)",
                    payload.station_code,
                    payload.recorded_at.isoformat(),
                    payload.source,
                )
                return duplicate
        raise

    created = await reading_repo.get_with_station(reading.id)
    logger.info("Persisted sensor reading for station %s", payload.station_code)
    if created is None:
        raise AppException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            code="sensor_reading_reload_failed",
            message="Reading was stored but could not be reloaded.",
        )
    return created


async def create_sensor_station(
    session: AsyncSession,
    payload: SensorStationCreate,
) -> object:
    """Create a sensor station."""
    region = await RegionRepository(session).get(payload.region_id)
    if region is None:
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="region_not_found",
            message=f"Region '{payload.region_id}' was not found.",
        )
    station_repo = SensorStationRepository(session)
    if await station_repo.get_by_code(payload.code) is not None:
        raise AppException(
            status_code=HTTPStatus.CONFLICT,
            code="sensor_station_code_exists",
            message=f"Sensor station '{payload.code}' already exists.",
        )
    station = await station_repo.add(
        SensorStation(
            region_id=payload.region_id,
            code=payload.code,
            name=payload.name,
            station_type=payload.station_type,
            status=payload.status,
            latitude=payload.latitude,
            longitude=payload.longitude,
            location_description=payload.location_description,
            installed_at=payload.installed_at,
            station_metadata=payload.station_metadata,
        )
    )
    await session.commit()
    await session.refresh(station)
    return station


async def list_sensor_stations(session: AsyncSession, *, limit: int = 100) -> list[object]:
    """List sensor stations."""
    return list(await SensorStationRepository(session).list_active(limit=limit))


async def get_sensor_station(session: AsyncSession, station_id: UUID) -> object:
    """Load a sensor station."""
    station = await SensorStationRepository(session).get(station_id)
    if station is None:
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="sensor_station_not_found",
            message=f"Sensor station '{station_id}' was not found.",
        )
    return station


async def update_sensor_station(
    session: AsyncSession,
    station_id: UUID,
    payload: SensorStationUpdate,
) -> object:
    """Update a station."""
    station = await get_sensor_station(session, station_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(station, field, value)
    await session.commit()
    await session.refresh(station)
    return station


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


def _is_duplicate_ingest_conflict(exc: IntegrityError) -> bool:
    """Detect sensor ingest uniqueness conflicts across DB drivers."""
    detail = f"{exc.orig!s} {exc!s}".lower()
    return (
        "uq_sensor_readings_station_recorded_source" in detail
        or "sensor_readings_station_id_recorded_at_source" in detail
        or "unique constraint" in detail
    )
