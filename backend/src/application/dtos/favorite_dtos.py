from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class AddFavoriteRequest(BaseModel):
    target_type: Literal["task", "hiver"]
    target_id: str


class FavoriteResponse(BaseModel):
    id: str
    user_id: str
    target_type: str
    target_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FavoriteIdsResponse(BaseModel):
    """The saved target ids per type, so the SPA can render hearts as filled."""

    tasks: list[str] = []
    hivers: list[str] = []
