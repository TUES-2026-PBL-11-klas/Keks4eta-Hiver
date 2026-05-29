from fastapi import APIRouter

from src.infrastructure.http.dependencies import SessionDep, ClientDep
from src.infrastructure.database.repositories.task_repository import PostgresTaskRepository
from src.infrastructure.database.repositories.transaction_repository import PostgresTransactionRepository
from src.application.use_cases.payments.release_escrow_use_case import ReleaseEscrowUseCase

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/tasks/{task_id}/release", status_code=200)
async def release_escrow(
    task_id: str,
    session: SessionDep,
    client: ClientDep,
) -> dict:
    use_case = ReleaseEscrowUseCase(
        task_repo=PostgresTaskRepository(session),
        transaction_repo=PostgresTransactionRepository(session),
    )
    return await use_case.execute(task_id=task_id, client_id=client.id)
