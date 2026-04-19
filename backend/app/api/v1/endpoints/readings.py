"""Canonical reading query endpoints."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.db.session import get_db_session
from app.schemas.common import SuccessResponse
from app.schemas.sensor import (
    SensorReadingCollection,
    SensorReadingHistoryFilters,
    SensorReadingRead,
)
from app.services.sensor_service import (
    list_latest_sensor_readings,
    list_sensor_reading_history,
)

router = APIRouter(prefix="/readings", tags=["readings"])


@router.get("/latest", response_model=SuccessResponse[SensorReadingCollection])
async def get_latest_readings(
    request: Request,
    station_id: UUID | None = Query(default=None),
    station_code: str | None = Query(default=None),
    region_id: UUID | None = Query(default=None),
    region_code: str | None = Query(default=None),
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db_session),
):
    """Return latest reading per station under canonical `/readings` namespace."""
    filters = SensorReadingHistoryFilters(
        station_id=station_id,
        station_code=station_code,
        region_id=region_id,
        region_code=region_code,
        start_at=start_at,
        end_at=end_at,
        limit=limit,
    )
    readings = await list_latest_sensor_readings(session, filters)
    payload = SensorReadingCollection(
        items=[SensorReadingRead.model_validate(reading) for reading in readings],
        count=len(readings),
    )
    return success_response(
        request=request,
        message="Latest readings retrieved successfully.",
        data=payload,
    )


@router.get("/history", response_model=SuccessResponse[SensorReadingCollection])
async def get_reading_history(
    request: Request,
    station_id: UUID | None = Query(default=None),
    station_code: str | None = Query(default=None),
    region_id: UUID | None = Query(default=None),
    region_code: str | None = Query(default=None),
    start_at: datetime | None = Query(default=None),
    end_at: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    session: AsyncSession = Depends(get_db_session),
):
    """Return historical readings under canonical `/readings` namespace."""
    filters = SensorReadingHistoryFilters(
        station_id=station_id,
        station_code=station_code,
        region_id=region_id,
        region_code=region_code,
        start_at=start_at,
        end_at=end_at,
        limit=limit,
    )
    readings = await list_sensor_reading_history(session, filters)
    payload = SensorReadingCollection(
        items=[SensorReadingRead.model_validate(reading) for reading in readings],
        count=len(readings),
    )
    return success_response(
        request=request,
        message="Reading history retrieved successfully.",
        data=payload,
    )
