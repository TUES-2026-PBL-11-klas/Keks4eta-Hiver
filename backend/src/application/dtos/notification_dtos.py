from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: str
    title: str
    body: str
    data: dict | None = None
    is_read: bool
    sent_at: datetime

    model_config = {"from_attributes": True}


class UnreadCountResponse(BaseModel):
    unread: int
