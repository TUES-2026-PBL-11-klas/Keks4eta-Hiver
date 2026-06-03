from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, field_validator


class OpenDisputeRequest(BaseModel):
    reason: str

    @field_validator("reason")
    @classmethod
    def reason_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Please describe the problem")
        return v.strip()


class ResolveDisputeRequest(BaseModel):
    note: str | None = None


class DisputeResponse(BaseModel):
    id: str
    task_id: str
    opened_by_id: str
    reason: str
    status: str  # open | resolved | refunded
    admin_note: str | None = None
    created_at: datetime
    resolved_at: datetime | None = None

    model_config = {"from_attributes": True}
