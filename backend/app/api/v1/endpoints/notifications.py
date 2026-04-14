"""Notification endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.db.session import get_db_session
from app.schemas.common import SuccessResponse
from app.schemas.notification import NotificationCollection, NotificationCreate, NotificationRead
from app.services.notification_service import create_notification, list_notifications, mark_notification_read

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("", response_model=SuccessResponse[NotificationRead], status_code=201)
async def create_notification_endpoint(
    payload: NotificationCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Create a mock notification."""
    notification = await create_notification(session, payload)
    await session.commit()
    await session.refresh(notification)
    return success_response(
        request=request,
        message="Notification sent successfully.",
        data=NotificationRead.model_validate(notification),
        status_code=201,
    )


@router.get("", response_model=SuccessResponse[NotificationCollection])
async def list_notification_endpoint(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    session: AsyncSession = Depends(get_db_session),
):
    """List notifications."""
    notifications = await list_notifications(session, limit=limit)
    return success_response(
        request=request,
        message="Notifications retrieved successfully.",
        data=NotificationCollection(
            items=[NotificationRead.model_validate(notification) for notification in notifications],
            count=len(notifications),
        ),
    )


@router.patch("/{notification_id}/read", response_model=SuccessResponse[NotificationRead])
async def mark_notification_read_endpoint(
    notification_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Mark notification as read for FE list semantics."""
    notification = await mark_notification_read(
        session,
        notification_id=notification_id,
        actor_name="operator",
    )
    return success_response(
        request=request,
        message="Notification marked as read successfully.",
        data=NotificationRead.model_validate(notification),
    )

