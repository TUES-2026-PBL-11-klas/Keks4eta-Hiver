from src.domain.errors.domain_errors import TaskNotFoundError
from src.domain.interfaces.repositories import ITaskRepository
from src.application.dtos.task_dtos import TaskDetailResponse


class GetTaskUseCase:
    def __init__(self, task_repo: ITaskRepository) -> None:
        self._task_repo = task_repo

    async def execute(self, task_id: str) -> TaskDetailResponse:
        task = await self._task_repo.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)

        return TaskDetailResponse(
            id=task.id,
            vertical=task.vertical,
            subcategory=task.subcategory,
            title=task.title,
            description=task.description,
            status=task.status.value,
            client_id=task.client_id,
            hiver_id=task.hiver_id,
            is_urgent=task.is_urgent,
            budget_min=float(task.budget_min.value) if task.budget_min else None,
            budget_max=float(task.budget_max.value) if task.budget_max else None,
            location_display=task.location.display_address if task.location else None,
            latitude=task.location.latitude if task.location else None,
            longitude=task.location.longitude if task.location else None,
            smart_answers=task.smart_answers,
            image_urls=task.image_urls,
            expires_at=task.expires_at,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
