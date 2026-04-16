"""Domain event append/read service for durable realtime streams."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain_event import DomainEvent
from app.repositories.domain_event import DomainEventRepository


async def append_domain_event(
    session: AsyncSession,
    *,
    event_type: str,
    source: str,
    summary: str,
    payload: dict[str, Any] | None = None,
    aggregate_type: str | None = None,
    aggregate_id: UUID | None = None,
    region_id: UUID | None = None,
    incident_id: UUID | None = None,
    action_plan_id: UUID | None = None,
    execution_batch_id: UUID | None = None,
) -> DomainEvent:
    """Append a domain event in the current transaction."""
    body = dict(payload or {})
    body.setdefault("summary", summary)
    event = DomainEvent(
        event_type=event_type,
        source=source,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        region_id=region_id,
        incident_id=incident_id,
        action_plan_id=action_plan_id,
        execution_batch_id=execution_batch_id,
        payload=body,
    )
    return await DomainEventRepository(session).add(event)


async def list_domain_events_after_cursor(
    session: AsyncSession,
    *,
    cursor: int,
    limit: int = 100,
) -> list[DomainEvent]:
    """List events strictly after cursor for stream catch-up."""
    return await DomainEventRepository(session).list_after_cursor(
        cursor=cursor,
        limit=limit,
    )


def to_stream_event_payload(event: DomainEvent) -> dict[str, Any]:
    """Serialize a domain event for SSE transport."""
    return {
        "cursor": event.sequence,
        "event_type": event.event_type,
        "summary": (event.payload or {}).get("summary"),
        "source": event.source,
        "aggregate_type": event.aggregate_type,
        "aggregate_id": str(event.aggregate_id) if event.aggregate_id is not None else None,
        "region_id": str(event.region_id) if event.region_id is not None else None,
        "payload": event.payload or {},
        "incident_id": str(event.incident_id) if event.incident_id is not None else None,
        "action_plan_id": str(event.action_plan_id) if event.action_plan_id is not None else None,
        "execution_batch_id": (
            str(event.execution_batch_id)
            if event.execution_batch_id is not None
            else None
        ),
        "occurred_at": event.occurred_at.isoformat() if event.occurred_at is not None else None,
    }
