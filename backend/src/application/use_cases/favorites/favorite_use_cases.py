import uuid

from src.application.dtos.favorite_dtos import FavoriteIdsResponse, FavoriteResponse
from src.application.dtos.task_dtos import TaskSummaryResponse
from src.application.dtos.user_dtos import HiverProfileResponse
from src.domain.entities.favorite import Favorite
from src.domain.entities.task import Task
from src.domain.entities.user import Hiver
from src.domain.interfaces.repositories import (
    IFavoriteRepository,
    IHiverRepository,
    ITaskRepository,
)


def _task_summary(t: Task) -> TaskSummaryResponse:
    return TaskSummaryResponse(
        id=t.id,
        vertical=t.vertical,
        subcategory=t.subcategory,
        title=t.title,
        status=t.status.value,
        is_urgent=t.is_urgent,
        budget_min=float(t.budget_min.value) if t.budget_min else None,
        budget_max=float(t.budget_max.value) if t.budget_max else None,
        location_display=t.location.display_address if t.location else None,
        latitude=t.location.latitude if t.location else None,
        longitude=t.location.longitude if t.location else None,
        is_featured=t.is_featured(),
        created_at=t.created_at,
    )


def _hiver_profile(h: Hiver) -> HiverProfileResponse:
    return HiverProfileResponse(
        user_id=h.id,
        full_name=h.full_name,
        email=h.email,
        avatar_url=h.avatar_url,
        bio=h.bio or "",
        level=h.level,
        xp_points=h.xp_points,
        avg_rating=float(h.avg_rating.value),
        completed_tasks=h.completed_tasks,
        review_count=h.review_count,
        is_available_now=h.is_available_now,
        work_radius_km=h.work_radius.km,
        skills=h.skills,
    )


class AddFavoriteUseCase:
    def __init__(self, favorite_repo: IFavoriteRepository) -> None:
        self._repo = favorite_repo

    async def execute(
        self, user_id: str, target_type: str, target_id: str
    ) -> FavoriteResponse:
        favorite = await self._repo.add(
            Favorite(
                id=str(uuid.uuid4()),
                user_id=user_id,
                target_type=target_type,
                target_id=target_id,
            )
        )
        return FavoriteResponse.model_validate(favorite)


class RemoveFavoriteUseCase:
    def __init__(self, favorite_repo: IFavoriteRepository) -> None:
        self._repo = favorite_repo

    async def execute(self, user_id: str, target_type: str, target_id: str) -> None:
        await self._repo.remove(user_id, target_type, target_id)


class ListFavoritesUseCase:
    """Resolves a user's saved ids back to full task/hiver cards, and exposes the
    raw id sets the SPA needs to render hearts as filled across every list."""

    def __init__(
        self,
        favorite_repo: IFavoriteRepository,
        task_repo: ITaskRepository,
        hiver_repo: IHiverRepository,
    ) -> None:
        self._repo = favorite_repo
        self._task_repo = task_repo
        self._hiver_repo = hiver_repo

    async def tasks(self, user_id: str) -> list[TaskSummaryResponse]:
        favorites = await self._repo.list_for_user(user_id, "task")
        out: list[TaskSummaryResponse] = []
        for fav in favorites:  # newest-first; skip anything since deleted
            task = await self._task_repo.find_by_id(fav.target_id)
            if task is not None:
                out.append(_task_summary(task))
        return out

    async def hivers(self, user_id: str) -> list[HiverProfileResponse]:
        favorites = await self._repo.list_for_user(user_id, "hiver")
        out: list[HiverProfileResponse] = []
        for fav in favorites:
            hiver = await self._hiver_repo.find_by_id(fav.target_id)
            if hiver is not None:
                out.append(_hiver_profile(hiver))
        return out

    async def ids(self, user_id: str) -> FavoriteIdsResponse:
        return FavoriteIdsResponse(
            tasks=await self._repo.target_ids(user_id, "task"),
            hivers=await self._repo.target_ids(user_id, "hiver"),
        )
