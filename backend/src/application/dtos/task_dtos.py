from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, field_validator, model_validator

VALID_VERTICALS = {"home", "learn", "tech", "care", "move", "events"}


class CreateTaskRequest(BaseModel):
    vertical: str
    subcategory: str
    title: str
    description: str
    smart_answers: dict[str, Any] = {}
    is_urgent: bool = False
    budget_min: float | None = None
    budget_max: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    location_display: str | None = None
    image_urls: list[str] = []

    @field_validator("vertical")
    @classmethod
    def valid_vertical(cls, v: str) -> str:
        if v not in VALID_VERTICALS:
            raise ValueError(f"vertical must be one of {VALID_VERTICALS}")
        return v

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title cannot be empty")
        return v.strip()

    @field_validator("budget_min", "budget_max")
    @classmethod
    def budget_non_negative(cls, v: float | None) -> float | None:
        if v is not None and v < 0:
            raise ValueError("budget cannot be negative")
        return v

    @model_validator(mode="after")
    def budget_range(self) -> CreateTaskRequest:
        if (
            self.budget_min is not None
            and self.budget_max is not None
            and self.budget_min > self.budget_max
        ):
            raise ValueError("budget_min cannot exceed budget_max")
        return self


class TaskSummaryResponse(BaseModel):
    id: str
    vertical: str
    subcategory: str
    title: str
    status: str
    is_urgent: bool
    budget_min: float | None
    budget_max: float | None
    location_display: str | None
    # Real coordinates (from PostGIS) so the SPA can drop a map pin per task.
    latitude: float | None = None
    longitude: float | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskDetailResponse(TaskSummaryResponse):
    description: str
    client_id: str
    hiver_id: str | None
    smart_answers: dict[str, Any]
    image_urls: list[str]
    expires_at: datetime | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class UpdateTaskStatusRequest(BaseModel):
    status: Literal["accepted", "in_progress", "completed", "cancelled"]
