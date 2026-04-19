"""Health endpoints."""

from typing import Literal

from fastapi import APIRouter, Query, Request

from app.core.responses import success_response
from app.schemas.common import SuccessResponse
from app.schemas.system import HealthPayload
from app.services.health_service import get_health_status

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=SuccessResponse[HealthPayload], summary="Health check")
async def health_check(
    request: Request,
    mode: Literal["liveness", "readiness"] = Query(default="liveness"),
):
    """Return service health payload with liveness/readiness modes."""
    payload = await get_health_status(mode=mode)
    message = (
        "Service readiness evaluated."
        if mode == "readiness"
        else "Service is healthy."
    )
    return success_response(
        request=request,
        message=message,
        data=payload,
    )

