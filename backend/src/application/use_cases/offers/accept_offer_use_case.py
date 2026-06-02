import uuid

from src.domain.errors.domain_errors import (
    TaskNotFoundError, OfferNotFoundError, UnauthorizedActionError,
)
from src.domain.entities.transaction import Transaction
from src.domain.interfaces.repositories import (
    ITaskRepository, IOfferRepository, ITransactionRepository,
)
from src.domain.interfaces.ports import IPaymentPort
from src.application.dtos.offer_dtos import OfferResponse


class AcceptOfferUseCase:
    """
    Accepting an offer simultaneously:
    - marks the offer as accepted
    - marks all other offers on the task as rejected
    - transitions the task to 'accepted'
    - holds the offer price in escrow (creates the Transaction)

    The escrow hold is the concrete side effect the codebase previously only
    described as a "Phase 5 TaskAccepted event": funds are captured the moment
    a client commits to a hiver, and only released after the work is confirmed.
    """

    def __init__(
        self,
        task_repo: ITaskRepository,
        offer_repo: IOfferRepository,
        transaction_repo: ITransactionRepository,
        payment_port: IPaymentPort,
    ) -> None:
        self._task_repo = task_repo
        self._offer_repo = offer_repo
        self._transaction_repo = transaction_repo
        self._payment_port = payment_port

    async def execute(self, task_id: str, offer_id: str, client_id: str) -> OfferResponse:
        task = await self._task_repo.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)

        if task.client_id != client_id:
            raise UnauthorizedActionError("accept offers for this task")

        offer = await self._offer_repo.find_by_id(offer_id)
        if offer is None or offer.task_id != task_id:
            raise OfferNotFoundError(offer_id)

        # Accept chosen offer
        offer.accept(client_id, task.client_id)
        await self._offer_repo.save(offer)

        # Reject all other pending offers on this task
        all_offers = await self._offer_repo.find_by_task(task_id)
        for other in all_offers:
            if other.id != offer_id and other.is_pending():
                other.reject(client_id, task.client_id)
                await self._offer_repo.save(other)

        # Transition task status
        task.accept(offer.hiver_id)
        await self._task_repo.save(task)

        # Escrow HOLD — capture the accepted offer price. The payment port returns
        # a (mock or real) intent id; the Transaction row is what release / refund
        # / the earnings view all operate on. Idempotent: skip if one exists.
        if await self._transaction_repo.find_by_task(task_id) is None:
            intent_id = await self._payment_port.hold_payment(offer.price, task.client_id)
            txn = Transaction.create_for_task(
                id=str(uuid.uuid4()),
                task_id=task_id,
                client_id=task.client_id,
                hiver_id=offer.hiver_id,
                offer_price=offer.price,
                stripe_payment_intent_id=intent_id,
            )
            await self._transaction_repo.save(txn)

        return OfferResponse(
            id=offer.id,
            task_id=offer.task_id,
            hiver_id=offer.hiver_id,
            price=float(offer.price.value),
            message=offer.message,
            estimated_hours=offer.estimated_hours,
            status=offer.status.value,
            created_at=offer.created_at,
        )
