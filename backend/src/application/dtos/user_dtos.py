from pydantic import BaseModel
from datetime import datetime


class ClientProfileResponse(BaseModel):
    user_id: str
    full_name: str
    email: str
    avatar_url: str | None
    rating_as_client: float
    total_tasks: int
    review_count: int

    model_config = {"from_attributes": True}


class HiverProfileResponse(BaseModel):
    user_id: str
    full_name: str
    email: str
    avatar_url: str | None
    bio: str
    level: str
    xp_points: int
    avg_rating: float
    completed_tasks: int
    review_count: int
    is_available_now: bool
    work_radius_km: int
    skills: list[str] = []

    model_config = {"from_attributes": True}


class UpdateHiverAvailabilityRequest(BaseModel):
    is_available_now: bool


class HiverSearchResult(BaseModel):
    user_id: str
    full_name: str
    avatar_url: str | None
    avg_rating: float
    level: str
    completed_tasks: int
    is_available_now: bool
    work_radius_km: int
    distance_km: float | None = None

    model_config = {"from_attributes": True}
