"""Notification endpoints.

GET    /api/v1/notifications           — List notifications (paginated)
GET    /api/v1/notifications/count     — Unread count
PUT    /api/v1/notifications/:id/read  — Mark as read
PUT    /api/v1/notifications/read-all  — Mark all as read
DELETE /api/v1/notifications/:id       — Delete notification
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.dependencies import get_current_user, get_db
from app.models.notification import Notification
from app.schemas.notifications import NotificationResponse

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("")
async def list_notifications(
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    type: str | None = None,
    is_read: bool | None = None,
):
    """List user's notifications, newest first."""
    user, _ = current_user

    query = select(Notification).where(Notification.user_id == user.id)
    count_query = select(func.count(Notification.id)).where(
        Notification.user_id == user.id
    )

    if type:
        query = query.where(Notification.type == type)
        count_query = count_query.where(Notification.type == type)
    if is_read is not None:
        query = query.where(Notification.is_read == is_read)
        count_query = count_query.where(Notification.is_read == is_read)

    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(query)
    notifications = result.scalars().all()

    return {
        "data": [
            NotificationResponse.model_validate(n).model_dump() for n in notifications
        ],
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": total,
            "has_more": offset + limit < total,
        },
    }


@router.get("/count")
async def unread_count(
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get unread notification count."""
    user, _ = current_user

    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == user.id,
            Notification.is_read == False,  # noqa: E712
        )
    )
    count = result.scalar() or 0
    return {"count": count}


@router.put("/read-all")
async def mark_all_read(
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Mark all unread notifications as read for the current user."""
    user, _ = current_user
    now = datetime.now(timezone.utc)

    result = await db.execute(
        update(Notification)
        .where(
            Notification.user_id == user.id, Notification.is_read == False
        )  # noqa: E712
        .values(is_read=True, read_at=now)
    )
    updated = result.rowcount

    logger.info(
        "notifications_marked_all_read",
        extra={"user_id": str(user.id), "count": updated},
    )
    return {"message": f"Marked {updated} notifications as read", "updated": updated}


@router.put("/{notification_id}/read")
async def mark_read(
    notification_id: uuid.UUID,
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Mark a single notification as read."""
    user, _ = current_user

    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )
    if notification.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your notification"
        )

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        logger.info(
            "notification_marked_read",
            extra={"user_id": str(user.id), "notification_id": str(notification_id)},
        )

    return NotificationResponse.model_validate(notification).model_dump()


@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_notification(
    notification_id: uuid.UUID,
    current_user: Annotated[Any, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a notification."""
    user, _ = current_user

    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found"
        )
    if notification.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not your notification"
        )

    await db.delete(notification)
    logger.info(
        "notification_deleted",
        extra={"user_id": str(user.id), "notification_id": str(notification_id)},
    )
