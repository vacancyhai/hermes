"""Pydantic schemas for notification endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    entity_type: str | None
    entity_id: uuid.UUID | None
    type: str
    title: str
    message: str
    action_url: str | None
    is_read: bool
    sent_via: list | None
    priority: str
    created_at: datetime
    read_at: datetime | None
    expires_at: datetime

    model_config = {"from_attributes": True}
