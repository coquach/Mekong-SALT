"""Risk read endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.responses import success_response
from app.db.session import get_db_session
from app.repositories.risk import RiskAssessmentRepository
from app.schemas.common import SuccessResponse
from app.schemas.risk import RiskAssessmentRead, RiskLatestResponse
from app.schemas.sensor import SensorReadingRead
from app.schemas.weather import WeatherSnapshotRead
from http import HTTPStatus

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get(
    "/latest",
    response_model=SuccessResponse[RiskLatestResponse],
    summary="Return latest persisted salinity risk",
)
async def get_latest_risk(
    request: Request,
    station_id: UUID | None = Query(default=None),
    station_code: str | None = Query(default=None),
    region_id: UUID | None = Query(default=None),
    region_code: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
):
    """Return the latest risk created by the reactive monitoring worker."""
    assessment = await RiskAssessmentRepository(session).get_latest(
        station_id=station_id,
        station_code=station_code,
        region_id=region_id,
        region_code=region_code,
    )
    if assessment is None:
        raise AppException(
            status_code=HTTPStatus.NOT_FOUND,
            code="risk_assessment_not_found",
            message="No risk assessment has been produced for the requested scope.",
        )
    payload = RiskLatestResponse(
        assessment=RiskAssessmentRead.model_validate(assessment),
        reading=(
            SensorReadingRead.model_validate(assessment.reading)
            if assessment.reading is not None
            else None
        ),
        weather_snapshot=(
            WeatherSnapshotRead.model_validate(assessment.weather_snapshot)
            if assessment.weather_snapshot is not None
            else None
        ),
    )
    return success_response(
        request=request,
        message="Latest risk retrieved successfully.",
        data=payload,
    )
