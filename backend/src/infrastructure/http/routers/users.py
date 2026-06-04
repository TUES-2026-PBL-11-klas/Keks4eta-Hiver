from fastapi import APIRouter, Query

from src.application.dtos.boost_dtos import BoostResponse, BuyBoostRequest
from src.application.dtos.review_dtos import ReviewResponse
from src.application.dtos.user_dtos import (
    ClientProfileResponse,
    HiverProfileResponse,
    HiverSearchResult,
    MeResponse,
    UpdateHiverAvailabilityRequest,
)
from src.application.use_cases.boosts.boost_use_cases import (
    BuyBoostUseCase,
    GetMyBoostUseCase,
)
from src.application.use_cases.reviews.list_reviews_use_case import (
    ListUserReviewsUseCase,
)
from src.application.use_cases.users.find_hivers_nearby_use_case import (
    FindHiversNearbyUseCase,
)
from src.domain.errors.domain_errors import ClientNotFoundError, HiverNotFoundError
from src.infrastructure.database.repositories.boost_repository import (
    PostgresBoostRepository,
)
from src.infrastructure.database.repositories.review_repository import (
    PostgresReviewRepository,
)
from src.infrastructure.database.repositories.user_repository import (
    PostgresClientRepository,
    PostgresHiverRepository,
)
from src.infrastructure.http.dependencies import HiverDep, SessionDep, UserPayloadDep
from src.infrastructure.payments.payment_factory import get_payment_port

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=MeResponse)
async def get_me(session: SessionDep, payload: UserPayloadDep) -> MeResponse:
    """Return the currently authenticated user with BOTH facets.

    Unified accounts: every account is both client and hiver, so the response
    carries the client stats and the hiver stats together.
    """
    user_id = payload["sub"]
    client = await PostgresClientRepository(session).find_by_id(user_id)
    hiver = await PostgresHiverRepository(session).find_by_id(user_id)
    base = client or hiver
    if base is None:
        raise ClientNotFoundError(user_id)

    return MeResponse(
        id=base.id,
        email=base.email,
        full_name=base.full_name,
        role="both",
        phone=base.phone,
        avatar_url=base.avatar_url,
        is_oauth=base.oauth_provider is not None,
        # hiver facet
        bio=(hiver.bio or "") if hiver else None,
        level=hiver.level if hiver else None,
        xp_points=hiver.xp_points if hiver else None,
        avg_rating=float(hiver.avg_rating.value) if hiver else None,
        completed_tasks=hiver.completed_tasks if hiver else None,
        is_available_now=hiver.is_available_now if hiver else None,
        work_radius_km=hiver.work_radius.km if hiver else None,
        skills=hiver.skills if hiver else [],
        # client facet
        rating_as_client=float(client.rating_as_client.value) if client else None,
        total_tasks=client.total_tasks if client else None,
        review_count=client.review_count if client else None,
    )


@router.get("/hivers/nearby", response_model=list[HiverSearchResult])
async def find_hivers_nearby(
    session: SessionDep,
    lat: float = Query(..., ge=-90.0, le=90.0, description="Latitude (WGS 84)"),
    lng: float = Query(..., ge=-180.0, le=180.0, description="Longitude (WGS 84)"),
    radius_km: float = Query(10.0, gt=0.0, le=100.0),
    vertical: str | None = Query(None, description="home|learn|tech|care|move|events"),
) -> list[HiverSearchResult]:
    use_case = FindHiversNearbyUseCase(
        hiver_repo=PostgresHiverRepository(session),
        boost_repo=PostgresBoostRepository(session),
    )
    return await use_case.execute(
        latitude=lat, longitude=lng, radius_km=radius_km, vertical=vertical
    )


@router.post("/hivers/me/boost", response_model=BoostResponse, status_code=201)
async def buy_boost(
    body: BuyBoostRequest,
    session: SessionDep,
    hiver: HiverDep,
) -> BoostResponse:
    use_case = BuyBoostUseCase(
        boost_repo=PostgresBoostRepository(session),
        payment_port=get_payment_port(),
    )
    return await use_case.execute(hiver_id=hiver.id, vertical=body.vertical)


@router.get("/hivers/me/boost", response_model=BoostResponse | None)
async def get_my_boost(
    session: SessionDep,
    hiver: HiverDep,
) -> BoostResponse | None:
    use_case = GetMyBoostUseCase(boost_repo=PostgresBoostRepository(session))
    return await use_case.execute(hiver_id=hiver.id)


@router.get("/clients/{client_id}", response_model=ClientProfileResponse)
async def get_client_profile(
    client_id: str, session: SessionDep
) -> ClientProfileResponse:
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
    boost = await PostgresBoostRepository(session).find_active_for_hiver(hiver_id)
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
        is_boosted=boost is not None,
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
