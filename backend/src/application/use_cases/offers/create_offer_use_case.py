import uuid
from src.domain.entities.offer import Offer
from src.domain.value_objects.money import Money
from src.domain.errors.domain_errors import (
    TaskNotFoundError, HiverNotFoundError,
    OfferAlreadyExistsError, TaskAlreadyAcceptedError,
)
from src.domain.interfaces.repositories import ITaskRepository, IOfferRepository, IHiverRepository
from src.application.dtos.offer_dtos import CreateOfferRequest, OfferResponse


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
    ) -> None:
        self._task_repo = task_repo
        self._offer_repo = offer_repo
        self._hiver_repo = hiver_repo

    async def execute(self, request: CreateOfferRequest, task_id: str, hiver_id: str) -> OfferResponse:
        task = await self._task_repo.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)

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
