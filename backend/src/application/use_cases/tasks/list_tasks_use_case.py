from src.application.dtos.task_dtos import TaskSummaryResponse
from src.domain.entities.task import Task
from src.domain.interfaces.repositories import ITaskRepository, PaginatedResult


def _to_summary(t: Task) -> TaskSummaryResponse:
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


class ListClientTasksUseCase:
    """Tasks the current user posted as a client."""

    def __init__(self, task_repo: ITaskRepository) -> None:
        self._task_repo = task_repo

    async def execute(
        self, client_id: str, page: int = 1, page_size: int = 20
    ) -> PaginatedResult[TaskSummaryResponse]:
        result = await self._task_repo.find_by_client(client_id, page, page_size)
        return PaginatedResult(
            items=[_to_summary(t) for t in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )


class ListAssignedTasksUseCase:
    """Tasks the current user is doing as a hiver (assigned to them)."""

    def __init__(self, task_repo: ITaskRepository) -> None:
        self._task_repo = task_repo

    async def execute(
        self, hiver_id: str, page: int = 1, page_size: int = 20
    ) -> PaginatedResult[TaskSummaryResponse]:
        result = await self._task_repo.find_by_hiver(hiver_id, page, page_size)
        return PaginatedResult(
            items=[_to_summary(t) for t in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )
