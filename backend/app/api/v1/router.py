"""V1 route composition."""

from fastapi import APIRouter

from app.api.v1.endpoints.alerts import router as alerts_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.risk import router as risk_router
from app.api.v1.endpoints.sensors import router as sensors_router

router = APIRouter()
router.include_router(alerts_router)
router.include_router(health_router)
router.include_router(risk_router)
router.include_router(sensors_router)

