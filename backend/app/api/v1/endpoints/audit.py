"""Audit log endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.db.session import get_db_session
from app.schemas.audit import AuditLogCollection, AuditLogRead
from app.schemas.common import SuccessResponse
from app.services.audit_service import list_audit_logs

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs", response_model=SuccessResponse[AuditLogCollection])
async def list_audit_log_endpoint(
    request: Request,
    incident_id: UUID | None = Query(default=None),
    plan_id: UUID | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db_session),
):
    """List audit logs."""
    logs = await list_audit_logs(session, incident_id=incident_id, plan_id=plan_id, limit=limit)
    return success_response(
        request=request,
        message="Audit logs retrieved successfully.",
        data=AuditLogCollection(
            items=[AuditLogRead.model_validate(log) for log in logs],
            count=len(logs),
        ),
    )

