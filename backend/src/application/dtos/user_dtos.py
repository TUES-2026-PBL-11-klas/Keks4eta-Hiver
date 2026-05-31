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


class MeResponse(BaseModel):
    """Current authenticated user — unified shape across roles.

    Role-specific fields are populated only for the matching role and are
    otherwise None, so the SPA can render one model regardless of role.
    """
    id: str
    email: str
    full_name: str
    role: str
    phone: str | None = None
    avatar_url: str | None = None
    is_oauth: bool = False
    # hiver-only
    bio: str | None = None
    level: str | None = None
    xp_points: int | None = None
    avg_rating: float | None = None
    completed_tasks: int | None = None
    is_available_now: bool | None = None
    work_radius_km: int | None = None
    skills: list[str] = []
    # client-only
    rating_as_client: float | None = None
    total_tasks: int | None = None
    review_count: int | None = None


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
