from fastapi import APIRouter

from src.application.dtos.offer_dtos import CreateOfferRequest, OfferResponse
from src.application.use_cases.offers.accept_offer_use_case import AcceptOfferUseCase
from src.application.use_cases.offers.create_offer_use_case import CreateOfferUseCase
from src.infrastructure.database.repositories.offer_repository import (
    PostgresOfferRepository,
)
from src.infrastructure.database.repositories.task_repository import (
    PostgresTaskRepository,
)
from src.infrastructure.database.repositories.transaction_repository import (
    PostgresTransactionRepository,
)
from src.infrastructure.database.repositories.user_repository import (
    PostgresHiverRepository,
)
from src.infrastructure.http.dependencies import (
    ClientDep,
    EventBusDep,
    HiverDep,
    SessionDep,
)
from src.infrastructure.payments.payment_factory import get_payment_port

router = APIRouter(tags=["offers"])


@router.post("/tasks/{task_id}/offers", response_model=OfferResponse, status_code=201)
async def create_offer(
    task_id: str,
    body: CreateOfferRequest,
    session: SessionDep,
    hiver: HiverDep,
    bus: EventBusDep,
) -> OfferResponse:
    use_case = CreateOfferUseCase(
        task_repo=PostgresTaskRepository(session),
        offer_repo=PostgresOfferRepository(session),
        hiver_repo=PostgresHiverRepository(session),
        event_bus=bus,
    )
    return await use_case.execute(body, task_id=task_id, hiver_id=hiver.id)


@router.get("/tasks/{task_id}/offers", response_model=list[OfferResponse])
async def list_task_offers(
    task_id: str,
    session: SessionDep,
    client: ClientDep,
) -> list[OfferResponse]:
    repo = PostgresOfferRepository(session)
    offers = await repo.find_by_task(task_id)
    return [
        OfferResponse(
            id=o.id,
            task_id=o.task_id,
            hiver_id=o.hiver_id,
            price=float(o.price.value),
            message=o.message,
            estimated_hours=o.estimated_hours,
            status=o.status.value,
            created_at=o.created_at,
        )
        for o in offers
    ]


@router.post(
    "/tasks/{task_id}/offers/{offer_id}/accept",
    response_model=OfferResponse,
)
async def accept_offer(
    task_id: str,
    offer_id: str,
    session: SessionDep,
    client: ClientDep,
    bus: EventBusDep,
) -> OfferResponse:
    use_case = AcceptOfferUseCase(
        task_repo=PostgresTaskRepository(session),
        offer_repo=PostgresOfferRepository(session),
        transaction_repo=PostgresTransactionRepository(session),
        payment_port=get_payment_port(),
        event_bus=bus,
    )
    return await use_case.execute(task_id=task_id, offer_id=offer_id, client_id=client.id)
