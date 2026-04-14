"""Risk evaluation endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.db.redis import RedisManager, get_redis_manager
from app.db.session import get_db_session
from app.schemas.common import SuccessResponse
from app.schemas.risk import RiskCurrentResponse, RiskEvaluationFilters
from app.schemas.risk import RiskAssessmentRead
from app.schemas.sensor import SensorReadingRead
from app.schemas.weather import WeatherSnapshotRead
from app.services.risk_service import evaluate_current_risk

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get(
    "/current",
    response_model=SuccessResponse[RiskCurrentResponse],
    summary="Evaluate current deterministic salinity risk",
)
async def get_current_risk(
    request: Request,
    station_id: UUID | None = Query(default=None),
    station_code: str | None = Query(default=None),
    region_id: UUID | None = Query(default=None),
    region_code: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
    redis_manager: RedisManager | None = Depends(get_redis_manager),
):
    """Evaluate and persist current risk for the requested scope."""
    filters = RiskEvaluationFilters(
        station_id=station_id,
        station_code=station_code,
        region_id=region_id,
        region_code=region_code,
    )
    bundle = await evaluate_current_risk(
        session,
        filters=filters,
        redis_manager=redis_manager,
    )
    payload = RiskCurrentResponse(
        assessment=RiskAssessmentRead.model_validate(bundle.assessment),
        reading=SensorReadingRead.model_validate(bundle.reading),
        weather_snapshot=(
            WeatherSnapshotRead.model_validate(bundle.weather_snapshot)
            if bundle.weather_snapshot is not None
            else None
        ),
        agent_run_id=bundle.run_id,
    )
    return success_response(
        request=request,
        message="Current risk evaluated successfully.",
        data=payload,
    )
