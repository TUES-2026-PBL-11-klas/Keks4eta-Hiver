from fastapi import APIRouter

from src.application.dtos.message_dtos import (
    ConversationResponse,
    MessageResponse,
    SendMessageRequest,
)
from src.application.use_cases.messages.message_use_cases import (
    ListConversationsUseCase,
    ListMessagesUseCase,
    SendMessageUseCase,
)
from src.infrastructure.database.repositories.message_repository import (
    PostgresMessageRepository,
)
from src.infrastructure.database.repositories.task_repository import (
    PostgresTaskRepository,
)
from src.infrastructure.database.repositories.user_repository import (
    PostgresClientRepository,
)
from src.infrastructure.http.dependencies import EventBusDep, SessionDep, UserPayloadDep

router = APIRouter(tags=["messages"])


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    session: SessionDep,
    payload: UserPayloadDep,
) -> list[ConversationResponse]:
    """The signed-in user's chat inbox — one row per task thread."""
    use_case = ListConversationsUseCase(
        message_repo=PostgresMessageRepository(session),
        task_repo=PostgresTaskRepository(session),
        client_repo=PostgresClientRepository(session),
    )
    return await use_case.execute(payload["sub"])


@router.get("/tasks/{task_id}/messages", response_model=list[MessageResponse])
async def list_messages(
    task_id: str,
    session: SessionDep,
    payload: UserPayloadDep,
) -> list[MessageResponse]:
    use_case = ListMessagesUseCase(
        task_repo=PostgresTaskRepository(session),
        message_repo=PostgresMessageRepository(session),
    )
    return await use_case.execute(task_id=task_id, reader_id=payload["sub"])


@router.post("/tasks/{task_id}/messages", response_model=MessageResponse, status_code=201)
async def send_message(
    task_id: str,
    body: SendMessageRequest,
    session: SessionDep,
    payload: UserPayloadDep,
    bus: EventBusDep,
) -> MessageResponse:
    use_case = SendMessageUseCase(
        task_repo=PostgresTaskRepository(session),
        message_repo=PostgresMessageRepository(session),
        event_bus=bus,
    )
    return await use_case.execute(
        task_id=task_id, sender_id=payload["sub"], content=body.content
    )
