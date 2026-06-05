from src.application.dtos.payment_dtos import EscrowResponse
from src.domain.errors.domain_errors import TaskNotFoundError, UnauthorizedActionError
from src.domain.interfaces.repositories import ITaskRepository, ITransactionRepository


class GetEscrowUseCase:
    """
    Read the escrow/transaction summary for a task.
    Visible only to the task's client or the assigned hiver.
    Returns None when no escrow has been created yet (task not accepted).
    """

    def __init__(
        self,
        task_repo: ITaskRepository,
        transaction_repo: ITransactionRepository,
    ) -> None:
        self._task_repo = task_repo
        self._transaction_repo = transaction_repo

    async def execute(self, task_id: str, user_id: str) -> EscrowResponse | None:
        task = await self._task_repo.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        if user_id not in (task.client_id, task.hiver_id):
            raise UnauthorizedActionError("view escrow for this task")

        txn = await self._transaction_repo.find_by_task(task_id)
        if txn is None:
            return None

        return EscrowResponse(
            task_id=txn.task_id,
            status=txn.status.value,
            gross_amount=float(txn.gross_amount.value),
            platform_fee=float(txn.platform_fee.value),
            hiver_payout=float(txn.hiver_payout.value),
            created_at=txn.created_at,
            released_at=txn.released_at,
            refunded_at=txn.refunded_at,
        )
