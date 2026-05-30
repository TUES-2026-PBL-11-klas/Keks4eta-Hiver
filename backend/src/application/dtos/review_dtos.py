from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class SubmitReviewRequest(BaseModel):
    rating: float = Field(..., ge=1.0, le=5.0, description="Stars 1.0–5.0")
    comment: str = Field(..., min_length=3, max_length=2000)

    @field_validator("comment")
    @classmethod
    def trim(cls, v: str) -> str:
        return v.strip()


class ReviewResponse(BaseModel):
    id: str
    task_id: str
    reviewer_id: str
    reviewee_id: str
    rating: float
    comment: str
    is_revealed: bool
    created_at: datetime

    model_config = {"from_attributes": True}
