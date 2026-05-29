from src.domain.services.task_factory import TaskFactory, TaskCreateData
from src.domain.errors.domain_errors import ClientNotFoundError
from src.domain.interfaces.repositories import ITaskRepository, IClientRepository
from src.application.dtos.task_dtos import CreateTaskRequest, TaskDetailResponse


class CreateTaskUseCase:
    """
    SOLID S: only creates tasks.
    SOLID D: depends on interfaces, not concrete repos.
    """

    def __init__(
        self,
        task_repo: ITaskRepository,
        client_repo: IClientRepository,
    ) -> None:
        self._task_repo = task_repo
        self._client_repo = client_repo

    async def execute(self, request: CreateTaskRequest, client_id: str) -> TaskDetailResponse:
        client = await self._client_repo.find_by_id(client_id)
        if client is None:
            raise ClientNotFoundError(client_id)

        client.assert_can_post_task()

        data = TaskCreateData(
            client_id=client_id,
            vertical=request.vertical,
            subcategory=request.subcategory,
            title=request.title,
            description=request.description,
            smart_answers=request.smart_answers,
            is_urgent=request.is_urgent,
            budget_min=request.budget_min,
            budget_max=request.budget_max,
            latitude=request.latitude,
            longitude=request.longitude,
            location_display=request.location_display,
            image_urls=request.image_urls,
        )
        task = TaskFactory.create(data)
        await self._task_repo.save(task)
        client.record_task_posted()
        await self._client_repo.save(client)

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
            smart_answers=task.smart_answers,
            image_urls=task.image_urls,
            expires_at=task.expires_at,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )
