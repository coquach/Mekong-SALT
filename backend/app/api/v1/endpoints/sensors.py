"""Sensor ingestion endpoints.

Read/query routes are served from `/readings/*`.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.db.session import get_db_session
from app.schemas.common import SuccessResponse
from app.schemas.sensor import SensorReadingIngestRequest, SensorReadingRead
from app.services.sensor_service import ingest_sensor_reading

router = APIRouter(prefix="/sensors", tags=["sensors"])


@router.post(
    "/ingest",
    response_model=SuccessResponse[SensorReadingRead],
    summary="Ingest a sensor reading",
)
async def ingest_reading(
    payload: SensorReadingIngestRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Validate and persist a single sensor reading."""
    reading = await ingest_sensor_reading(session, payload)
    return success_response(
        request=request,
        message="Sensor reading ingested successfully.",
        data=SensorReadingRead.model_validate(reading),
        status_code=201,
    )
