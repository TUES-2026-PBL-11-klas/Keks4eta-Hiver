from src.domain.errors.domain_errors import (
    TaskNotFoundError, TransactionNotFoundError, UnauthorizedActionError,
    TaskNotCompletedError,
)
from src.domain.entities.task import TaskStatus
from src.domain.interfaces.repositories import ITaskRepository, ITransactionRepository
from src.domain.interfaces.ports import IPaymentPort
from src.domain.services.event_bus import EventBus, notify


class ReleaseEscrowUseCase:
    """
    Client confirms the task is done → releases held funds to the hiver.

    Robust to either UI flow: the client may release straight from IN_PROGRESS
    (we confirm completion here) or after a separate /complete call. Captures the
    held payment via the payment port, then flips the Transaction to RELEASED —
    which is what the hiver_earnings_monthly view counts.
    SOLID S: only handles escrow release.
    """

    def __init__(
        self,
        task_repo: ITaskRepository,
        transaction_repo: ITransactionRepository,
        payment_port: IPaymentPort,
        event_bus: EventBus | None = None,
    ) -> None:
        self._task_repo = task_repo
        self._transaction_repo = transaction_repo
        self._payment_port = payment_port
        self._event_bus = event_bus

    async def execute(self, task_id: str, client_id: str) -> dict:
        task = await self._task_repo.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)

        if task.client_id != client_id:
            raise UnauthorizedActionError("release escrow for this task")

        transaction = await self._transaction_repo.find_by_task(task_id)
        if transaction is None:
            raise TransactionNotFoundError(task_id)

        # Confirm completion if releasing straight from in_progress; otherwise the
        # task must already be completed (a separate /complete call ran first).
        if task.status == TaskStatus.IN_PROGRESS:
            task.complete(client_id)
            await self._task_repo.save(task)
        elif task.status != TaskStatus.COMPLETED:
            raise TaskNotCompletedError(task_id)

        # Capture the held funds (mock = no-op; Stripe = capture the PaymentIntent).
        await self._payment_port.release_payment(transaction.stripe_payment_intent_id)
        transaction.release()
        await self._transaction_repo.save(transaction)

        await notify(
            self._event_bus,
            transaction.hiver_id,
            "Payment released",
            f"{float(transaction.hiver_payout.value):.2f} BGN was released to you for '{task.title}'.",
            {"task_id": task_id},
        )

        return {
            "task_id": task_id,
            "status": "released",
            "hiver_payout": float(transaction.hiver_payout.value),
        }
