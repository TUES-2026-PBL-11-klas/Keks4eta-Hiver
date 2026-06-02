from src.domain.errors.domain_errors import TaskNotFoundError
from src.domain.interfaces.repositories import ITaskRepository, ITransactionRepository
from src.domain.interfaces.ports import IPaymentPort
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
    Any escrow already held for the task is refunded back to the client.
    The escrow deps are optional so the use case still works for tasks cancelled
    while still OPEN (no transaction yet) and in unit tests without payments.
    """

    def __init__(
        self,
        task_repo: ITaskRepository,
        transaction_repo: ITransactionRepository | None = None,
        payment_port: IPaymentPort | None = None,
    ) -> None:
        self._task_repo = task_repo
        self._transaction_repo = transaction_repo
        self._payment_port = payment_port

    async def execute(self, task_id: str, actor_id: str) -> TaskDetailResponse:
        task = await self._task_repo.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        task.cancel(actor_id=actor_id)
        await self._task_repo.save(task)

        # Refund any held escrow back to the client.
        if self._transaction_repo is not None:
            txn = await self._transaction_repo.find_by_task(task_id)
            if txn is not None and txn.is_held():
                if self._payment_port is not None:
                    await self._payment_port.refund_payment(
                        txn.stripe_payment_intent_id, txn.gross_amount
                    )
                txn.refund()
                await self._transaction_repo.save(txn)

        return await GetTaskUseCase(self._task_repo).execute(task_id)
