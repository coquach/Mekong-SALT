"""Health endpoints."""

from fastapi import APIRouter, Request

from app.core.responses import success_response
from app.schemas.common import SuccessResponse
from app.schemas.system import HealthPayload
from app.services.health_service import get_health_status

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=SuccessResponse[HealthPayload], summary="Health check")
async def health_check(request: Request):
    """Return a simple service health payload."""
    payload = get_health_status()
    return success_response(
        request=request,
        message="Service is healthy.",
        data=payload,
    )

