from typing import Literal

from fastapi import APIRouter

from src.application.dtos.favorite_dtos import (
    AddFavoriteRequest,
    FavoriteIdsResponse,
    FavoriteResponse,
)
from src.application.dtos.task_dtos import TaskSummaryResponse
from src.application.dtos.user_dtos import HiverProfileResponse
from src.application.use_cases.favorites.favorite_use_cases import (
    AddFavoriteUseCase,
    ListFavoritesUseCase,
    RemoveFavoriteUseCase,
)
from src.infrastructure.database.repositories.favorite_repository import (
    PostgresFavoriteRepository,
)
from src.infrastructure.database.repositories.task_repository import (
    PostgresTaskRepository,
)
from src.infrastructure.database.repositories.user_repository import (
    PostgresHiverRepository,
)
from src.infrastructure.http.dependencies import SessionDep, UserPayloadDep

router = APIRouter(prefix="/favorites", tags=["favorites"])


def _list_use_case(session: SessionDep) -> ListFavoritesUseCase:
    return ListFavoritesUseCase(
        favorite_repo=PostgresFavoriteRepository(session),
        task_repo=PostgresTaskRepository(session),
        hiver_repo=PostgresHiverRepository(session),
    )


@router.post("", response_model=FavoriteResponse, status_code=201)
async def add_favorite(
    body: AddFavoriteRequest,
    session: SessionDep,
    payload: UserPayloadDep,
) -> FavoriteResponse:
    """Save a task or hiver. Idempotent — saving twice returns the same row."""
    use_case = AddFavoriteUseCase(PostgresFavoriteRepository(session))
    return await use_case.execute(payload["sub"], body.target_type, body.target_id)


@router.delete("/{target_type}/{target_id}", status_code=204)
async def remove_favorite(
    target_type: Literal["task", "hiver"],
    target_id: str,
    session: SessionDep,
    payload: UserPayloadDep,
) -> None:
    """Unsave a task or hiver. No-op if it wasn't saved."""
    use_case = RemoveFavoriteUseCase(PostgresFavoriteRepository(session))
    await use_case.execute(payload["sub"], target_type, target_id)


@router.get("/tasks", response_model=list[TaskSummaryResponse])
async def list_favorite_tasks(
    session: SessionDep, payload: UserPayloadDep
) -> list[TaskSummaryResponse]:
    return await _list_use_case(session).tasks(payload["sub"])


@router.get("/hivers", response_model=list[HiverProfileResponse])
async def list_favorite_hivers(
    session: SessionDep, payload: UserPayloadDep
) -> list[HiverProfileResponse]:
    return await _list_use_case(session).hivers(payload["sub"])


@router.get("/ids", response_model=FavoriteIdsResponse)
async def list_favorite_ids(
    session: SessionDep, payload: UserPayloadDep
) -> FavoriteIdsResponse:
    """Just the saved ids per type — the SPA fills hearts from this."""
    return await _list_use_case(session).ids(payload["sub"])
