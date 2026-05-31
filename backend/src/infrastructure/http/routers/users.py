from fastapi import APIRouter, Query

from src.infrastructure.http.dependencies import SessionDep, HiverDep, UserPayloadDep
from src.infrastructure.database.repositories.user_repository import (
    PostgresClientRepository,
    PostgresHiverRepository,
)
from src.domain.errors.domain_errors import ClientNotFoundError, HiverNotFoundError
from src.application.dtos.user_dtos import (
    ClientProfileResponse,
    HiverProfileResponse,
    UpdateHiverAvailabilityRequest,
    HiverSearchResult,
    MeResponse,
)
from src.application.use_cases.users.find_hivers_nearby_use_case import (
    FindHiversNearbyUseCase,
)
from src.application.use_cases.reviews.list_reviews_use_case import (
    ListUserReviewsUseCase,
)
from src.application.dtos.review_dtos import ReviewResponse
from src.infrastructure.database.repositories.review_repository import (
    PostgresReviewRepository,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=MeResponse)
async def get_me(session: SessionDep, payload: UserPayloadDep) -> MeResponse:
    """Return the currently authenticated user (role-aware)."""
    user_id = payload["sub"]
    if payload.get("role") == "hiver":
        hiver = await PostgresHiverRepository(session).find_by_id(user_id)
        if hiver is None:
            raise HiverNotFoundError(user_id)
        return MeResponse(
            id=hiver.id,
            email=hiver.email,
            full_name=hiver.full_name,
            role="hiver",
            phone=hiver.phone,
            avatar_url=hiver.avatar_url,
            is_oauth=hiver.oauth_provider is not None,
            bio=hiver.bio or "",
            level=hiver.level,
            xp_points=hiver.xp_points,
            avg_rating=float(hiver.avg_rating.value),
            completed_tasks=hiver.completed_tasks,
            review_count=hiver.review_count,
            is_available_now=hiver.is_available_now,
            work_radius_km=hiver.work_radius.km,
            skills=hiver.skills,
        )

    client = await PostgresClientRepository(session).find_by_id(user_id)
    if client is None:
        raise ClientNotFoundError(user_id)
    return MeResponse(
        id=client.id,
        email=client.email,
        full_name=client.full_name,
        role="client",
        phone=client.phone,
        avatar_url=client.avatar_url,
        is_oauth=client.oauth_provider is not None,
        rating_as_client=float(client.rating_as_client.value),
        total_tasks=client.total_tasks,
        review_count=client.review_count,
    )


@router.get("/hivers/nearby", response_model=list[HiverSearchResult])
async def find_hivers_nearby(
    session: SessionDep,
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude (WGS 84)"),
    lng: float = Query(..., ge=-180.0, le=180.0, description="Longitude (WGS 84)"),
    radius_km: float = Query(10.0, gt=0.0, le=100.0),
    vertical: str | None = Query(None, description="home|learn|tech|care|move|events"),
) -> list[HiverSearchResult]:
    use_case = FindHiversNearbyUseCase(hiver_repo=PostgresHiverRepository(session))
    return await use_case.execute(
        latitude=lat, longitude=lng, radius_km=radius_km, vertical=vertical
    )


@router.get("/clients/{client_id}", response_model=ClientProfileResponse)
async def get_client_profile(client_id: str, session: SessionDep) -> ClientProfileResponse:
    client = await PostgresClientRepository(session).find_by_id(client_id)
    if client is None:
        raise ClientNotFoundError(client_id)
    return ClientProfileResponse(
        user_id=client.id,
        full_name=client.full_name,
        email=client.email,
        avatar_url=client.avatar_url,
        rating_as_client=float(client.rating_as_client.value),
        total_tasks=client.total_tasks,
        review_count=client.review_count,
    )


@router.get("/hivers/{hiver_id}", response_model=HiverProfileResponse)
async def get_hiver_profile(hiver_id: str, session: SessionDep) -> HiverProfileResponse:
    hiver = await PostgresHiverRepository(session).find_by_id(hiver_id)
    if hiver is None:
        raise HiverNotFoundError(hiver_id)
    return HiverProfileResponse(
        user_id=hiver.id,
        full_name=hiver.full_name,
        email=hiver.email,
        avatar_url=hiver.avatar_url,
        bio=hiver.bio or "",
        level=hiver.level,
        xp_points=hiver.xp_points,
        avg_rating=float(hiver.avg_rating.value),
        completed_tasks=hiver.completed_tasks,
        review_count=hiver.review_count,
        is_available_now=hiver.is_available_now,
        work_radius_km=hiver.work_radius.km,
        skills=hiver.skills,
    )


@router.get("/{user_id}/reviews", response_model=list[ReviewResponse])
async def list_user_reviews(user_id: str, session: SessionDep) -> list[ReviewResponse]:
    use_case = ListUserReviewsUseCase(review_repo=PostgresReviewRepository(session))
    return await use_case.execute(user_id=user_id)


@router.patch("/hivers/me/availability", response_model=HiverProfileResponse)
async def update_my_availability(
    body: UpdateHiverAvailabilityRequest,
    session: SessionDep,
    hiver: HiverDep,
) -> HiverProfileResponse:
    hiver.is_available_now = body.is_available_now
    await PostgresHiverRepository(session).save(hiver)
    return HiverProfileResponse(
        user_id=hiver.id,
        full_name=hiver.full_name,
        email=hiver.email,
        avatar_url=hiver.avatar_url,
        bio=hiver.bio or "",
        level=hiver.level,
        xp_points=hiver.xp_points,
        avg_rating=float(hiver.avg_rating.value),
        completed_tasks=hiver.completed_tasks,
        review_count=hiver.review_count,
        is_available_now=hiver.is_available_now,
        work_radius_km=hiver.work_radius.km,
        skills=hiver.skills,
    )
