"""Incident management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.db.session import get_db_session
from app.models.enums import IncidentStatus
from app.schemas.common import SuccessResponse
from app.schemas.incident import IncidentCollection, IncidentCreate, IncidentRead, IncidentUpdate
from app.services.incident_service import create_incident, get_incident, list_incidents, update_incident_status

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.post("", response_model=SuccessResponse[IncidentRead], status_code=201)
async def create_incident_endpoint(
    payload: IncidentCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Create a manual incident."""
    incident = await create_incident(session, payload, actor_name="operator")
    return success_response(
        request=request,
        message="Incident created successfully.",
        data=IncidentRead.model_validate(incident),
        status_code=201,
    )


@router.get("", response_model=SuccessResponse[IncidentCollection])
async def list_incident_endpoint(
    request: Request,
    status: IncidentStatus | None = Query(default=None),
    region_id: UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db_session),
):
    """List incidents."""
    incidents = await list_incidents(session, status=status, region_id=region_id, limit=limit)
    return success_response(
        request=request,
        message="Incidents retrieved successfully.",
        data=IncidentCollection(
            items=[IncidentRead.model_validate(incident) for incident in incidents],
            count=len(incidents),
        ),
    )


@router.get("/{incident_id}", response_model=SuccessResponse[IncidentRead])
async def get_incident_endpoint(
    incident_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Get incident detail."""
    incident = await get_incident(session, incident_id)
    return success_response(
        request=request,
        message="Incident retrieved successfully.",
        data=IncidentRead.model_validate(incident),
    )


@router.patch("/{incident_id}", response_model=SuccessResponse[IncidentRead])
async def update_incident_endpoint(
    incident_id: UUID,
    payload: IncidentUpdate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Update incident status."""
    incident = await update_incident_status(
        session,
        incident_id,
        payload,
        actor_name="operator",
    )
    return success_response(
        request=request,
        message="Incident updated successfully.",
        data=IncidentRead.model_validate(incident),
    )
