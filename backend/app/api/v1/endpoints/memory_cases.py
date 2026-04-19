"""Memory case browsing endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.db.session import get_db_session
from app.repositories.memory_case import MemoryCaseRepository
from app.schemas.common import SuccessResponse
from app.schemas.memory_case import MemoryCaseCollection, MemoryCaseRead

router = APIRouter(prefix="/memory-cases", tags=["memory-cases"])


@router.get("", response_model=SuccessResponse[MemoryCaseCollection])
async def list_memory_cases(
    request: Request,
    region_id: UUID | None = Query(default=None),
    station_id: UUID | None = Query(default=None),
    severity: str | None = Query(default=None),
    q: str | None = Query(default=None, description="Search objective, summary, keywords and payloads."),
    limit: int = Query(default=24, ge=1, le=200),
    session: AsyncSession = Depends(get_db_session),
):
    """List recent memory cases for the dedicated UI page."""
    memory_cases = await MemoryCaseRepository(session).list_recent(
        limit=limit,
        region_id=region_id,
        station_id=station_id,
        severity=severity,
        query=q,
    )
    return success_response(
        request=request,
        message="Memory cases retrieved successfully.",
        data=MemoryCaseCollection(
            items=[MemoryCaseRead.model_validate(memory_case) for memory_case in memory_cases],
            count=len(memory_cases),
        ),
    )