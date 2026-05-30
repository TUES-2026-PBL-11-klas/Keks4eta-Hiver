from src.domain.errors.domain_errors import TaskNotFoundError
from src.domain.interfaces.repositories import ITaskRepository
from src.application.use_cases.tasks.get_task_use_case import GetTaskUseCase
from src.application.dtos.task_dtos import TaskDetailResponse


class StartTaskUseCase:
    """
    Hiver transitions task ACCEPTED → IN_PROGRESS.
    Domain entity enforces actor + state validity.
    """

    def __init__(self, task_repo: ITaskRepository) -> None:
        self._task_repo = task_repo

    async def execute(self, task_id: str, hiver_id: str) -> TaskDetailResponse:
        task = await self._task_repo.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        task.start(actor_id=hiver_id)
        await self._task_repo.save(task)
        return await GetTaskUseCase(self._task_repo).execute(task_id)
