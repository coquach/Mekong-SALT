"""V1 route composition."""

from fastapi import APIRouter

from app.api.v1.endpoints.actions import router as actions_router
from app.api.v1.endpoints.agent import router as agent_router
from app.api.v1.endpoints.audit import router as audit_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.execution_batches import router as execution_batches_router
from app.api.v1.endpoints.goals import router as goals_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.incidents import router as incidents_router
from app.api.v1.endpoints.notifications import router as notifications_router
from app.api.v1.endpoints.plans import router as plans_router
from app.api.v1.endpoints.readings import router as readings_router
from app.api.v1.endpoints.risk import router as risk_router
from app.api.v1.endpoints.sensors import router as sensors_router
from app.api.v1.endpoints.stations import router as stations_router

router = APIRouter()
router.include_router(actions_router)
router.include_router(agent_router)
router.include_router(audit_router)
router.include_router(dashboard_router)
router.include_router(execution_batches_router)
router.include_router(goals_router)
router.include_router(health_router)
router.include_router(incidents_router)
router.include_router(notifications_router)
router.include_router(plans_router)
router.include_router(readings_router)
# Legacy routers stay registered during FE migration to new facade paths.
router.include_router(risk_router)
router.include_router(sensors_router)
router.include_router(stations_router)

