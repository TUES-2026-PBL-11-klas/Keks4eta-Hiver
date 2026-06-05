from pydantic import BaseModel, Field, field_validator, model_validator

from src.domain.value_objects.work_radius import ALLOWED_RADII_KM


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
    latitude: float | None = None
    longitude: float | None = None
    location_display: str | None = None
    is_boosted: bool = False

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
    latitude: float | None = None
    longitude: float | None = None
    location_display: str | None = None
    # client-only
    rating_as_client: float | None = None
    total_tasks: int | None = None
    review_count: int | None = None


class UpdateHiverAvailabilityRequest(BaseModel):
    is_available_now: bool


class UpdateMeRequest(BaseModel):
    """Partial profile edit (PATCH /users/me).

    Every field is optional with PATCH semantics: a field left ``None`` is not
    touched. Strings can be cleared by sending an empty value (e.g. ``bio=""``);
    skills can be cleared with ``[]``. Coordinates must arrive as a pair.
    """

    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    bio: str | None = Field(default=None, max_length=1000)
    skills: list[str] | None = None
    work_radius_km: int | None = None
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    location_display: str | None = Field(default=None, max_length=255)

    @field_validator("work_radius_km")
    @classmethod
    def _radius_in_allowed_tiers(cls, v: int | None) -> int | None:
        if v is not None and v not in ALLOWED_RADII_KM:
            raise ValueError(f"work_radius_km must be one of {ALLOWED_RADII_KM}")
        return v

    @model_validator(mode="after")
    def _coords_come_as_pair(self) -> "UpdateMeRequest":
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must be provided together")
        return self


class HiverSearchResult(BaseModel):
    user_id: str
    full_name: str
    avatar_url: str | None
    avg_rating: float
    level: str
    completed_tasks: int
    is_available_now: bool
    work_radius_km: int
    latitude: float | None = None
    longitude: float | None = None
    distance_km: float | None = None
    is_boosted: bool = False

    model_config = {"from_attributes": True}
