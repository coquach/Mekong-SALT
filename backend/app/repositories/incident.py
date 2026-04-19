"""Repositories for incident management."""

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import IncidentStatus, RiskLevel
from app.models.incident import Incident
from app.repositories.base import AsyncRepository


class IncidentRepository(AsyncRepository[Incident]):
    """Incident query helpers."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Incident)

    async def get_open_for_assessment(self, risk_assessment_id: UUID) -> Incident | None:
        """Return an open incident already created from an assessment."""
        result = await self.session.scalars(
            select(Incident)
            .where(
                Incident.risk_assessment_id == risk_assessment_id,
                Incident.status.not_in([IncidentStatus.RESOLVED, IncidentStatus.CLOSED]),
            )
            .order_by(desc(Incident.opened_at))
            .limit(1)
        )
        return result.first()

    async def get_open_by_region_and_severity(
        self,
        region_id: UUID,
        severity: RiskLevel,
    ) -> Incident | None:
        """Return an active incident in the same region/severity bucket."""
        result = await self.session.scalars(
            select(Incident)
            .where(
                Incident.region_id == region_id,
                Incident.severity == severity,
                Incident.status.not_in([IncidentStatus.RESOLVED, IncidentStatus.CLOSED]),
            )
            .order_by(desc(Incident.opened_at))
            .limit(1)
        )
        return result.first()

    async def list_recent(
        self,
        *,
        status: IncidentStatus | None = None,
        region_id: UUID | None = None,
        limit: int = 100,
    ) -> list[Incident]:
        """Return recent incidents."""
        statement = select(Incident).order_by(desc(Incident.opened_at), desc(Incident.created_at))
        if status is not None:
            statement = statement.where(Incident.status == status)
        if region_id is not None:
            statement = statement.where(Incident.region_id == region_id)
        result = await self.session.scalars(statement.limit(limit))
        return list(result.all())

