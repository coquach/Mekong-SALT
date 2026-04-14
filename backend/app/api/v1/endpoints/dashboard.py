"""Dashboard endpoints."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.db.session import AsyncSessionFactory, get_db_session
from app.schemas.common import SuccessResponse
from app.schemas.dashboard import DashboardSummary, DashboardTimeline
from app.services.dashboard_service import get_dashboard_summary, get_dashboard_timeline

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=SuccessResponse[DashboardSummary])
async def dashboard_summary(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return dashboard summary data."""
    payload = await get_dashboard_summary(session)
    return success_response(
        request=request,
        message="Dashboard summary retrieved successfully.",
        data=payload,
    )


@router.get("/timeline", response_model=SuccessResponse[DashboardTimeline])
async def dashboard_timeline(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return a compact timeline series for FE dashboard charts."""
    payload = await get_dashboard_timeline(session)
    return success_response(
        request=request,
        message="Dashboard timeline retrieved successfully.",
        data=payload,
    )


@router.get("/stream")
async def dashboard_stream(request: Request):
    """Server-Sent Events stream for dashboard refreshes."""

    async def _events():
        while not await request.is_disconnected():
            async with AsyncSessionFactory() as session:
                summary = await get_dashboard_summary(session)
            yield f"event: summary\ndata: {json.dumps(summary.model_dump(mode='json'))}\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(_events(), media_type="text/event-stream")
