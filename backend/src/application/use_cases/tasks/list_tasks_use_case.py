from src.application.dtos.task_dtos import TaskSummaryResponse
from src.domain.interfaces.repositories import ITaskRepository, PaginatedResult


class ListClientTasksUseCase:
    def __init__(self, task_repo: ITaskRepository) -> None:
        self._task_repo = task_repo

    async def execute(
        self, client_id: str, page: int = 1, page_size: int = 20
    ) -> PaginatedResult[TaskSummaryResponse]:
        result = await self._task_repo.find_by_client(client_id, page, page_size)
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
                created_at=t.created_at,
            )
            for t in result.items
        ]
        return PaginatedResult(
            items=items, total=result.total, page=result.page, page_size=result.page_size
        )
