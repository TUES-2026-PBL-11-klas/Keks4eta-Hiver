from fastapi import APIRouter

from src.application.dtos.payment_dtos import EscrowResponse
from src.application.use_cases.payments.get_escrow_use_case import GetEscrowUseCase
from src.application.use_cases.payments.release_escrow_use_case import (
    ReleaseEscrowUseCase,
)
from src.infrastructure.database.repositories.task_repository import (
    PostgresTaskRepository,
)
from src.infrastructure.database.repositories.transaction_repository import (
    PostgresTransactionRepository,
)
from src.infrastructure.http.dependencies import (
    ClientDep,
    EventBusDep,
    SessionDep,
    UserPayloadDep,
)
from src.infrastructure.payments.payment_factory import get_payment_port

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("/tasks/{task_id}", response_model=EscrowResponse | None)
async def get_escrow(
    task_id: str,
    session: SessionDep,
    payload: UserPayloadDep,
) -> EscrowResponse | None:
    use_case = GetEscrowUseCase(
        task_repo=PostgresTaskRepository(session),
        transaction_repo=PostgresTransactionRepository(session),
    )
    return await use_case.execute(task_id=task_id, user_id=payload["sub"])


@router.post("/tasks/{task_id}/release", status_code=200)
async def release_escrow(
    task_id: str,
    session: SessionDep,
    client: ClientDep,
    bus: EventBusDep,
) -> dict:
    use_case = ReleaseEscrowUseCase(
        task_repo=PostgresTaskRepository(session),
        transaction_repo=PostgresTransactionRepository(session),
        payment_port=get_payment_port(),
        event_bus=bus,
    )
    return await use_case.execute(task_id=task_id, client_id=client.id)
