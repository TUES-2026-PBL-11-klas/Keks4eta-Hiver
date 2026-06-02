import uuid

from src.domain.entities.dispute import Dispute
from src.domain.entities.task import Task
from src.domain.errors.domain_errors import (
    TaskNotFoundError, UnauthorizedActionError, TransactionNotFoundError,
    DisputeAlreadyExistsError, DisputeNotFoundError, NoEscrowToDisputeError,
)
from src.domain.interfaces.repositories import (
    ITaskRepository, IDisputeRepository, ITransactionRepository,
)
from src.domain.interfaces.ports import IPaymentPort
from src.domain.services.event_bus import EventBus, notify
from src.application.dtos.dispute_dtos import DisputeResponse


def _role(task: Task, user_id: str) -> str:
    """Return 'client' or 'hiver' for a participant; raise otherwise."""
    if user_id == task.client_id:
        return "client"
    if task.hiver_id is not None and user_id == task.hiver_id:
        return "hiver"
    raise UnauthorizedActionError("access this dispute")


def _to_response(d: Dispute) -> DisputeResponse:
    return DisputeResponse(
        id=d.id,
        task_id=d.task_id,
        opened_by_id=d.opened_by_id,
        reason=d.reason,
        status=d.status.value,
        admin_note=d.admin_note,
        created_at=d.created_at,
        resolved_at=d.resolved_at,
    )


class OpenDisputeUseCase:
    def __init__(
        self,
        task_repo: ITaskRepository,
        dispute_repo: IDisputeRepository,
        transaction_repo: ITransactionRepository,
        event_bus: EventBus | None = None,
    ) -> None:
        self._task_repo = task_repo
        self._dispute_repo = dispute_repo
        self._transaction_repo = transaction_repo
        self._event_bus = event_bus

    async def execute(self, task_id: str, user_id: str, reason: str) -> DisputeResponse:
        task = await self._task_repo.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        role = _role(task, user_id)

        txn = await self._transaction_repo.find_by_task(task_id)
        if txn is None or not txn.is_held():
            raise NoEscrowToDisputeError(task_id)

        if await self._dispute_repo.find_by_task(task_id) is not None:
            raise DisputeAlreadyExistsError(task_id)

        dispute = await self._dispute_repo.add(
            Dispute(id=str(uuid.uuid4()), task_id=task_id, opened_by_id=user_id, reason=reason)
        )

        task.open_dispute()
        await self._task_repo.save(task)
        txn.dispute()
        await self._transaction_repo.save(txn)

        # Notify the counterparty.
        recipient = task.hiver_id if role == "client" else task.client_id
        if recipient:
            await notify(
                self._event_bus,
                recipient,
                "Dispute opened",
                f"A problem was reported on '{task.title}'. Funds are held until it's resolved.",
                {"task_id": task_id},
            )

        return _to_response(dispute)


class ResolveDisputeUseCase:
    """
    Resolution by concession:
      - the client concedes  → release escrow to the hiver, task COMPLETED
      - the hiver concedes    → refund escrow to the client, task CANCELLED
    Neither party can grant money to themselves.
    """

    def __init__(
        self,
        task_repo: ITaskRepository,
        dispute_repo: IDisputeRepository,
        transaction_repo: ITransactionRepository,
        payment_port: IPaymentPort,
        event_bus: EventBus | None = None,
    ) -> None:
        self._task_repo = task_repo
        self._dispute_repo = dispute_repo
        self._transaction_repo = transaction_repo
        self._payment_port = payment_port
        self._event_bus = event_bus

    async def execute(self, task_id: str, user_id: str, note: str | None = None) -> DisputeResponse:
        task = await self._task_repo.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        role = _role(task, user_id)

        dispute = await self._dispute_repo.find_by_task(task_id)
        if dispute is None:
            raise DisputeNotFoundError(task_id)

        txn = await self._transaction_repo.find_by_task(task_id)
        if txn is None:
            raise TransactionNotFoundError(task_id)

        if role == "client":
            # Client concedes → release to hiver.
            await self._payment_port.release_payment(txn.stripe_payment_intent_id)
            txn.release()
            await self._transaction_repo.save(txn)
            task.resolve_dispute(release=True)
            await self._task_repo.save(task)
            dispute.resolve_release(note)
            await self._dispute_repo.save(dispute)
            await notify(
                self._event_bus, task.hiver_id or "",
                "Dispute resolved",
                f"The client released your payment for '{task.title}'.",
                {"task_id": task_id},
            )
        else:
            # Hiver concedes → refund to client.
            await self._payment_port.refund_payment(txn.stripe_payment_intent_id, txn.gross_amount)
            txn.refund()
            await self._transaction_repo.save(txn)
            task.resolve_dispute(release=False)
            await self._task_repo.save(task)
            dispute.resolve_refund(note)
            await self._dispute_repo.save(dispute)
            await notify(
                self._event_bus, task.client_id,
                "Dispute resolved",
                f"The hiver refunded your payment for '{task.title}'.",
                {"task_id": task_id},
            )

        return _to_response(dispute)


class GetDisputeUseCase:
    def __init__(self, task_repo: ITaskRepository, dispute_repo: IDisputeRepository) -> None:
        self._task_repo = task_repo
        self._dispute_repo = dispute_repo

    async def execute(self, task_id: str, user_id: str) -> DisputeResponse | None:
        task = await self._task_repo.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        _role(task, user_id)  # participants only
        dispute = await self._dispute_repo.find_by_task(task_id)
        return _to_response(dispute) if dispute else None
