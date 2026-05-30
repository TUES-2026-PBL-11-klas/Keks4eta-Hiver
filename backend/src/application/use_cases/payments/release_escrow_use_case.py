from src.domain.errors.domain_errors import TaskNotFoundError, TransactionNotFoundError, UnauthorizedActionError
from src.domain.interfaces.repositories import ITaskRepository, ITransactionRepository


class ReleaseEscrowUseCase:
    """
    Client confirms task done → releases held funds to hiver.
    SOLID S: only handles escrow release.
    """

    def __init__(
        self,
        task_repo: ITaskRepository,
        transaction_repo: ITransactionRepository,
    ) -> None:
        self._task_repo = task_repo
        self._transaction_repo = transaction_repo

    async def execute(self, task_id: str, client_id: str) -> dict:
        task = await self._task_repo.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)

        if task.client_id != client_id:
            raise UnauthorizedActionError("release escrow for this task")

        transaction = await self._transaction_repo.find_by_task(task_id)
        if transaction is None:
            raise TransactionNotFoundError(task_id)

        transaction.release()
        await self._transaction_repo.save(transaction)

        task.complete(client_id)
        await self._task_repo.save(task)

        return {
            "task_id": task_id,
            "status": "released",
            "hiver_payout": float(transaction.hiver_payout.value),
        }
