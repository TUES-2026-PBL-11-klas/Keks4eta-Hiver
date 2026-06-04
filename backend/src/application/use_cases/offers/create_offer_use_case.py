import uuid

from src.application.dtos.offer_dtos import CreateOfferRequest, OfferResponse
from src.domain.entities.offer import Offer
from src.domain.errors.domain_errors import (
    CannotOfferOnOwnTaskError,
    HiverNotFoundError,
    OfferAlreadyExistsError,
    TaskAlreadyAcceptedError,
    TaskNotFoundError,
)
from src.domain.interfaces.repositories import (
    IHiverRepository,
    IOfferRepository,
    ITaskRepository,
)
from src.domain.services.event_bus import EventBus, notify
from src.domain.value_objects.money import Money


class CreateOfferUseCase:
    """
    SOLID S: only creates offers.
    SOLID D: depends on ITaskRepository, IOfferRepository, IHiverRepository.
    """

    def __init__(
        self,
        task_repo: ITaskRepository,
        offer_repo: IOfferRepository,
        hiver_repo: IHiverRepository,
        event_bus: EventBus | None = None,
    ) -> None:
        self._task_repo = task_repo
        self._offer_repo = offer_repo
        self._hiver_repo = hiver_repo
        self._event_bus = event_bus

    async def execute(self, request: CreateOfferRequest, task_id: str, hiver_id: str) -> OfferResponse:
        task = await self._task_repo.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)

        # Unified accounts can both post and work — but never on their own task.
        if task.client_id == hiver_id:
            raise CannotOfferOnOwnTaskError(task_id)

        if not task.is_open():
            raise TaskAlreadyAcceptedError(task_id)

        hiver = await self._hiver_repo.find_by_id(hiver_id)
        if hiver is None:
            raise HiverNotFoundError(hiver_id)

        existing = await self._offer_repo.find_by_task_and_hiver(task_id, hiver_id)
        if existing:
            raise OfferAlreadyExistsError(hiver_id, task_id)

        offer = Offer(
            id=str(uuid.uuid4()),
            task_id=task_id,
            hiver_id=hiver_id,
            price=Money.of(request.price),
            message=request.message,
            estimated_hours=request.estimated_hours,
        )
        await self._offer_repo.save(offer)

        await notify(
            self._event_bus,
            task.client_id,
            "New offer on your task",
            f"{hiver.full_name} offered {request.price:.0f} BGN on '{task.title}'.",
            {"task_id": task_id, "offer_id": offer.id},
        )

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
