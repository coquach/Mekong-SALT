"""Health service for system readiness metadata."""

from app.core.config import get_settings
from app.schemas.system import HealthPayload


def get_health_status() -> HealthPayload:
    """Return a lightweight service health payload.

    Phase 1 only reports configuration presence, not dependency reachability.
    """
    settings = get_settings()
    return HealthPayload(
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        dependencies={
            "database": "configured",
            "redis": "configured",
        },
    )

