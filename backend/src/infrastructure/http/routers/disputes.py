from fastapi import APIRouter

from src.application.dtos.dispute_dtos import (
    DisputeResponse,
    OpenDisputeRequest,
    ResolveDisputeRequest,
)
from src.application.use_cases.disputes.dispute_use_cases import (
    GetDisputeUseCase,
    OpenDisputeUseCase,
    ResolveDisputeUseCase,
)
from src.infrastructure.database.repositories.dispute_repository import (
    PostgresDisputeRepository,
)
from src.infrastructure.database.repositories.task_repository import (
    PostgresTaskRepository,
)
from src.infrastructure.database.repositories.transaction_repository import (
    PostgresTransactionRepository,
)
from src.infrastructure.http.dependencies import EventBusDep, SessionDep, UserPayloadDep
from src.infrastructure.payments.payment_factory import get_payment_port

router = APIRouter(tags=["disputes"])


@router.get("/tasks/{task_id}/disputes", response_model=DisputeResponse | None)
async def get_dispute(
    task_id: str,
    session: SessionDep,
    payload: UserPayloadDep,
) -> DisputeResponse | None:
    use_case = GetDisputeUseCase(
        task_repo=PostgresTaskRepository(session),
        dispute_repo=PostgresDisputeRepository(session),
    )
    return await use_case.execute(task_id=task_id, user_id=payload["sub"])


@router.post("/tasks/{task_id}/disputes", response_model=DisputeResponse, status_code=201)
async def open_dispute(
    task_id: str,
    body: OpenDisputeRequest,
    session: SessionDep,
    payload: UserPayloadDep,
    bus: EventBusDep,
) -> DisputeResponse:
    use_case = OpenDisputeUseCase(
        task_repo=PostgresTaskRepository(session),
        dispute_repo=PostgresDisputeRepository(session),
        transaction_repo=PostgresTransactionRepository(session),
        event_bus=bus,
    )
    return await use_case.execute(task_id=task_id, user_id=payload["sub"], reason=body.reason)


@router.post("/tasks/{task_id}/disputes/resolve", response_model=DisputeResponse)
async def resolve_dispute(
    task_id: str,
    body: ResolveDisputeRequest,
    session: SessionDep,
    payload: UserPayloadDep,
    bus: EventBusDep,
) -> DisputeResponse:
    use_case = ResolveDisputeUseCase(
        task_repo=PostgresTaskRepository(session),
        dispute_repo=PostgresDisputeRepository(session),
        transaction_repo=PostgresTransactionRepository(session),
        payment_port=get_payment_port(),
        event_bus=bus,
    )
    return await use_case.execute(task_id=task_id, user_id=payload["sub"], note=body.note)
