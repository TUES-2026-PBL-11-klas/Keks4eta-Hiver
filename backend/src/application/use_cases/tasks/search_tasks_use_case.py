from src.application.dtos.task_dtos import TaskSummaryResponse
from src.domain.interfaces.repositories import ITaskRepository, PaginatedResult


class SearchTasksUseCase:
    """
    Public task search with optional filters.
    OOP: Single Responsibility — orchestrates filter assembly only;
         the repository owns the query.
    """

    def __init__(self, task_repo: ITaskRepository) -> None:
        self._task_repo = task_repo

    async def execute(
        self,
        vertical: str | None = None,
        status: str | None = None,
        is_urgent: bool | None = None,
        min_budget: float | None = None,
        max_budget: float | None = None,
        q: str | None = None,
        lat: float | None = None,
        lng: float | None = None,
        radius_km: float | None = None,
        sort: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResult[TaskSummaryResponse]:
        result = await self._task_repo.search(
            vertical=vertical,
            status=status,
            is_urgent=is_urgent,
            min_budget=min_budget,
            max_budget=max_budget,
            q=q,
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            sort=sort,
            page=page,
            page_size=page_size,
        )
        items = [
            TaskSummaryResponse(
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
                created_at=t.created_at,
            )
            for t in result.items
        ]
        return PaginatedResult(
            items=items, total=result.total, page=result.page, page_size=result.page_size
        )
