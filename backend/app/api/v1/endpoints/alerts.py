"""Alert evaluation endpoints."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.db.redis import RedisManager, get_redis_manager
from app.db.session import get_db_session
from app.schemas.common import SuccessResponse
from app.schemas.risk import (
    AlertEvaluationResponse,
    AlertEventRead,
    RiskAssessmentRead,
    RiskEvaluationFilters,
)
from app.schemas.sensor import SensorReadingRead
from app.schemas.weather import WeatherSnapshotRead
from app.services.risk_service import evaluate_alerts

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post(
    "/evaluate",
    response_model=SuccessResponse[AlertEvaluationResponse],
    summary="Evaluate risk and create an alert when needed",
)
async def evaluate_alert_endpoint(
    payload: RiskEvaluationFilters,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
    redis_manager: RedisManager | None = Depends(get_redis_manager),
):
    """Evaluate the current risk and create an alert when thresholds require it."""
    bundle = await evaluate_alerts(
        session,
        filters=payload,
        redis_manager=redis_manager,
    )
    response_payload = AlertEvaluationResponse(
        assessment=RiskAssessmentRead.model_validate(bundle.assessment),
        reading=SensorReadingRead.model_validate(bundle.reading),
        weather_snapshot=(
            WeatherSnapshotRead.model_validate(bundle.weather_snapshot)
            if bundle.weather_snapshot is not None
            else None
        ),
        alert=(
            AlertEventRead.model_validate(bundle.alert)
            if bundle.alert is not None
            else None
        ),
        alert_created=bundle.alert_created,
        agent_run_id=bundle.run_id,
    )
    return success_response(
        request=request,
        message="Alert evaluation completed successfully.",
        data=response_payload,
    )
