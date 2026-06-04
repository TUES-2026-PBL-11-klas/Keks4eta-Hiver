from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, field_validator


class SendMessageRequest(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()


class MessageResponse(BaseModel):
    id: str
    task_id: str
    sender_id: str
    content: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}
