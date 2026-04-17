"""Dashboard endpoints."""

from __future__ import annotations

import asyncio
import json
import time
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.responses import success_response
from app.db.redis import RedisManager, get_redis_manager
from app.db.session import AsyncSessionFactory, get_db_session
from app.repositories.region import RegionRepository
from app.repositories.sensor import SensorStationRepository
from app.schemas.common import SuccessResponse
from app.schemas.dashboard import (
    DashboardEarthEngineLatest,
    DashboardSummary,
    DashboardTimeline,
)
from app.services.db import (
    list_domain_events_after_cursor,
    to_stream_event_payload,
)
from app.services.dashboard_service import (
    get_dashboard_summary,
    get_dashboard_timeline,
    get_latest_earth_engine_context,
)

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


@router.get(
    "/earth-engine/latest",
    response_model=SuccessResponse[DashboardEarthEngineLatest],
)
async def dashboard_earth_engine_latest(
    request: Request,
    station_id: UUID | None = Query(default=None),
    station_code: str | None = Query(default=None),
    region_id: UUID | None = Query(default=None),
    region_code: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db_session),
):
    """Return latest persisted Earth Engine context captured in planning runs."""
    station_repo = SensorStationRepository(session)
    region_repo = RegionRepository(session)
    resolved_station_id = station_id
    resolved_region_id = region_id

    station = None
    region = None
    if station_code is not None:
        station = await station_repo.get_by_code(station_code)
        if station is None:
            raise AppException(
                status_code=HTTPStatus.NOT_FOUND,
                code="sensor_station_not_found",
                message=f"Sensor station '{station_code}' was not found.",
            )
        resolved_station_id = station.id
    elif station_id is not None:
        station = await station_repo.get(station_id)
        if station is None:
            raise AppException(
                status_code=HTTPStatus.NOT_FOUND,
                code="sensor_station_not_found",
                message=f"Sensor station '{station_id}' was not found.",
            )

    if region_code is not None:
        region = await region_repo.get_by_code(region_code)
        if region is None:
            raise AppException(
                status_code=HTTPStatus.NOT_FOUND,
                code="region_not_found",
                message=f"Region '{region_code}' was not found.",
            )
        resolved_region_id = region.id
    elif region_id is not None:
        region = await region_repo.get(region_id)
        if region is None:
            raise AppException(
                status_code=HTTPStatus.NOT_FOUND,
                code="region_not_found",
                message=f"Region '{region_id}' was not found.",
            )

    if station is not None and region is not None and station.region_id != region.id:
        raise AppException(
            status_code=HTTPStatus.BAD_REQUEST,
            code="station_region_mismatch",
            message="station and region filters do not refer to the same region.",
        )

    payload = await get_latest_earth_engine_context(
        session,
        station_id=resolved_station_id,
        region_id=resolved_region_id,
    )
    return success_response(
        request=request,
        message="Latest Earth Engine context retrieved successfully.",
        data=payload,
    )


@router.get("/stream")
async def dashboard_stream(
    request: Request,
    cursor: int | None = Query(default=None, ge=0),
    redis_manager: RedisManager | None = Depends(get_redis_manager),
):
    """Server-Sent Events stream with durable cursor-based event delivery."""

    header_cursor = _parse_cursor(request.headers.get("last-event-id"))
    start_cursor = max(cursor if cursor is not None else header_cursor, 0)

    async def _events():
        current_cursor = start_cursor
        last_summary_at = 0.0
        poll_interval_seconds = 1.5
        summary_interval_seconds = 12.0
        signal_channel = get_settings().domain_event_signal_channel

        yield "retry: 2000\n\n"
        while not await request.is_disconnected():
            emitted = False
            async with AsyncSessionFactory() as session:
                events = await list_domain_events_after_cursor(
                    session,
                    cursor=current_cursor,
                    limit=100,
                )

                for event in events:
                    current_cursor = event.sequence
                    emitted = True
                    yield _format_sse(
                        event_name="domain_event",
                        data=to_stream_event_payload(event),
                        cursor=current_cursor,
                    )

                now = time.monotonic()
                should_emit_summary = (
                    not emitted
                    and (now - last_summary_at) >= summary_interval_seconds
                )
                if should_emit_summary:
                    summary = await get_dashboard_summary(session)
                    emitted = True
                    last_summary_at = now
                    yield _format_sse(
                        event_name="summary",
                        data={
                            "cursor": current_cursor,
                            "fallback": True,
                            "summary": summary.model_dump(mode="json"),
                        },
                        cursor=current_cursor,
                    )

            if not emitted:
                yield ": keepalive\n\n"
                if redis_manager is not None:
                    await redis_manager.wait_for_signal(
                        signal_channel,
                        timeout_seconds=poll_interval_seconds,
                    )
                else:
                    await asyncio.sleep(poll_interval_seconds)
            else:
                await asyncio.sleep(0)

    return StreamingResponse(_events(), media_type="text/event-stream")


def _format_sse(*, event_name: str, data: dict, cursor: int) -> str:
    lines = [f"event: {event_name}"]
    if cursor > 0:
        lines.append(f"id: {cursor}")
    lines.append(f"data: {json.dumps(data)}")
    return "\n".join(lines) + "\n\n"


def _parse_cursor(raw: str | None) -> int:
    if raw is None:
        return 0
    try:
        value = int(raw)
    except ValueError:
        return 0
    return max(value, 0)
