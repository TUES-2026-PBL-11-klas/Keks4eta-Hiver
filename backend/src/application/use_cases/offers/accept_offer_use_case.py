from src.domain.errors.domain_errors import (
    TaskNotFoundError, OfferNotFoundError, UnauthorizedActionError,
)
from src.domain.interfaces.repositories import ITaskRepository, IOfferRepository
from src.application.dtos.offer_dtos import OfferResponse


class AcceptOfferUseCase:
    """
    Accepting an offer simultaneously:
    - marks the offer as accepted
    - marks all other offers on the task as rejected
    - transitions the task to 'accepted'

    Observer pattern: in Phase 5 this would publish a TaskAccepted event
    to trigger escrow hold and notification.
    """

    def __init__(
        self,
        task_repo: ITaskRepository,
        offer_repo: IOfferRepository,
    ) -> None:
        self._task_repo = task_repo
        self._offer_repo = offer_repo

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
