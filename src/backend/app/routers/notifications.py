"""Notification endpoints.

GET    /api/v1/notifications           — List notifications
GET    /api/v1/notifications/count     — Unread count
PUT    /api/v1/notifications/:id/read  — Mark as read
PUT    /api/v1/notifications/read-all  — Mark all as read
DELETE /api/v1/notifications/:id       — Delete notification
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


@router.get("")
async def list_notifications():
    """List user's notifications. TODO: Implement."""
    return {"data": [], "pagination": {"limit": 20, "offset": 0, "total": 0, "has_more": False}}


@router.get("/count")
async def unread_count():
    """Get unread notification count. TODO: Implement."""
    return {"count": 0}


@router.put("/{notification_id}/read")
async def mark_read(notification_id: str):
    """Mark a notification as read. TODO: Implement."""
    return {"message": "Not implemented"}


@router.put("/read-all")
async def mark_all_read():
    """Mark all notifications as read. TODO: Implement."""
    return {"message": "Not implemented"}


@router.delete("/{notification_id}")
async def delete_notification(notification_id: str):
    """Delete a notification. TODO: Implement."""
    return {"message": "Not implemented"}
