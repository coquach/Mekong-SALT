"""Gate management services."""

from http import HTTPStatus
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.models.gate import Gate
from app.repositories.gate import GateRepository
from app.repositories.region import RegionRepository
from app.repositories.sensor import SensorStationRepository
from app.schemas.gate import GateCreate, GateUpdate


async def create_gate(session: AsyncSession, payload: GateCreate) -> Gate:
    """Create a gate record."""
    region = await RegionRepository(session).get(payload.region_id)
    if region is None:
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="region_not_found",
            message=f"Vùng '{payload.region_id}' không tồn tại.",
        )

    station_repo = SensorStationRepository(session)
    if payload.station_id is not None:
        station = await station_repo.get(payload.station_id)
        if station is None:
            raise AppException(
                status_code=HTTPStatus.NOT_FOUND,
                code="sensor_station_not_found",
                message=f"Trạm cảm biến '{payload.station_id}' không tồn tại.",
            )
        if station.region_id != payload.region_id:
            raise AppException(
                status_code=HTTPStatus.CONFLICT,
                code="gate_station_region_mismatch",
                message="Trạm cảm biến phải thuộc cùng vùng với cống.",
            )

    gate_repo = GateRepository(session)
    existing = await gate_repo.get_by_code(payload.code)
    if existing is not None:
        raise AppException(
            status_code=HTTPStatus.CONFLICT,
            code="gate_code_exists",
            message=f"Cống '{payload.code}' đã tồn tại.",
        )

    gate = await gate_repo.add(
        Gate(
            region_id=payload.region_id,
            station_id=payload.station_id,
            code=payload.code,
            name=payload.name,
            gate_type=payload.gate_type,
            status=payload.status,
            latitude=payload.latitude,
            longitude=payload.longitude,
            location_description=payload.location_description,
            last_operated_at=payload.last_operated_at,
            gate_metadata=payload.gate_metadata,
        )
    )
    await session.commit()
    reloaded = await gate_repo.get_with_station(gate.id)
    if reloaded is None:
        raise AppException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            code="gate_reload_failed",
            message="Cống đã được lưu nhưng không thể tải lại.",
        )
    return reloaded


async def get_gate(session: AsyncSession, gate_id: UUID) -> Gate:
    """Load a gate by primary key."""
    gate = await GateRepository(session).get_with_station(gate_id)
    if gate is None:
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="gate_not_found",
            message=f"Cống '{gate_id}' không tồn tại.",
        )
    return gate


async def list_gates(
    session: AsyncSession,
    *,
    limit: int = 100,
    region_code: str | None = None,
) -> list[Gate]:
    """List gates, optionally filtered by region code."""
    gate_repo = GateRepository(session)
    if region_code is None:
        return list(await gate_repo.list_all(limit=limit))

    region = await RegionRepository(session).get_by_code(region_code)
    if region is None:
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="region_not_found",
            message=f"Vùng '{region_code}' không tồn tại.",
        )
    return list(await gate_repo.list_by_region(region.id, limit=limit))


async def update_gate(session: AsyncSession, gate_id: UUID, payload: GateUpdate) -> Gate:
    """Apply a partial gate update."""
    gate = await get_gate(session, gate_id)
    updates = payload.model_dump(exclude_unset=True)

    if "code" in updates and updates["code"] is not None:
        existing = await GateRepository(session).get_by_code(updates["code"])
        if existing is not None and existing.id != gate.id:
            raise AppException(
                status_code=HTTPStatus.CONFLICT,
                code="gate_code_exists",
                message=f"Cống '{updates['code']}' đã tồn tại.",
            )

    if "station_id" in updates and updates["station_id"] is not None:
        station = await SensorStationRepository(session).get(updates["station_id"])
        if station is None:
            raise AppException(
                status_code=HTTPStatus.NOT_FOUND,
                code="sensor_station_not_found",
                message=f"Trạm cảm biến '{updates['station_id']}' không tồn tại.",
            )
        if station.region_id != gate.region_id:
            raise AppException(
                status_code=HTTPStatus.CONFLICT,
                code="gate_station_region_mismatch",
                message="Trạm cảm biến phải thuộc cùng vùng với cống.",
            )

    for field, value in updates.items():
        setattr(gate, field, value)

    await session.commit()
    reloaded = await GateRepository(session).get_with_station(gate.id)
    if reloaded is None:
        raise AppException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            code="gate_reload_failed",
            message="Cống đã được cập nhật nhưng không thể tải lại.",
        )
    return reloaded
