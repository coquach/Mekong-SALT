"""Station management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.db.session import get_db_session
from app.schemas.common import SuccessResponse
from app.schemas.sensor import (
    SensorStationCollection,
    SensorStationCreate,
    SensorStationRead,
    SensorStationUpdate,
)
from app.services.sensor_service import (
    create_sensor_station,
    get_sensor_station,
    list_sensor_stations,
    update_sensor_station,
)

router = APIRouter(prefix="/stations", tags=["stations"])


@router.post("", response_model=SuccessResponse[SensorStationRead], status_code=201)
async def create_station(
    payload: SensorStationCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Register a station."""
    station = await create_sensor_station(session, payload)
    return success_response(
        request=request,
        message="Station created successfully.",
        data=SensorStationRead.model_validate(station),
        status_code=201,
    )


@router.get("", response_model=SuccessResponse[SensorStationCollection])
async def list_stations(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db_session),
):
    """List stations."""
    stations = await list_sensor_stations(session, limit=limit)
    return success_response(
        request=request,
        message="Stations retrieved successfully.",
        data=SensorStationCollection(
            items=[SensorStationRead.model_validate(station) for station in stations],
            count=len(stations),
        ),
    )


@router.get("/{station_id}", response_model=SuccessResponse[SensorStationRead])
async def get_station(
    station_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Get a station."""
    station = await get_sensor_station(session, station_id)
    return success_response(
        request=request,
        message="Station retrieved successfully.",
        data=SensorStationRead.model_validate(station),
    )


@router.patch("/{station_id}", response_model=SuccessResponse[SensorStationRead])
async def update_station(
    station_id: UUID,
    payload: SensorStationUpdate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Update a station."""
    station = await update_sensor_station(session, station_id, payload)
    return success_response(
        request=request,
        message="Station updated successfully.",
        data=SensorStationRead.model_validate(station),
    )

