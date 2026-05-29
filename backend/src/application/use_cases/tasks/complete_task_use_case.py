from src.domain.errors.domain_errors import TaskNotFoundError
from src.domain.interfaces.repositories import ITaskRepository
from src.application.use_cases.tasks.get_task_use_case import GetTaskUseCase
from src.application.dtos.task_dtos import TaskDetailResponse


class CompleteTaskUseCase:
    """
    Client transitions task IN_PROGRESS → COMPLETED.
    Triggers escrow release in a separate use case (Observer pattern, Phase 5).
    """

    def __init__(self, task_repo: ITaskRepository) -> None:
        self._task_repo = task_repo

    async def execute(self, task_id: str, client_id: str) -> TaskDetailResponse:
        task = await self._task_repo.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        task.complete(actor_id=client_id)
        await self._task_repo.save(task)
        return await GetTaskUseCase(self._task_repo).execute(task_id)


class CancelTaskUseCase:
    """
    Client or assigned Hiver cancels a task before it completes.
    """

    def __init__(self, task_repo: ITaskRepository) -> None:
        self._task_repo = task_repo

    async def execute(self, task_id: str, actor_id: str) -> TaskDetailResponse:
        task = await self._task_repo.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        task.cancel(actor_id=actor_id)
        await self._task_repo.save(task)
        return await GetTaskUseCase(self._task_repo).execute(task_id)
