from fastapi import APIRouter, WebSocket, WebSocketDisconnect

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
from src.domain.errors.domain_errors import AppError
from src.infrastructure.database.repositories.message_repository import (
    PostgresMessageRepository,
)
from src.infrastructure.database.repositories.task_repository import (
    PostgresTaskRepository,
)
from src.infrastructure.database.repositories.user_repository import (
    PostgresClientRepository,
)
from src.infrastructure.database.session import AsyncSessionLocal
from src.infrastructure.http.chat_hub import chat_hub
from src.infrastructure.http.dependencies import EventBusDep, SessionDep, UserPayloadDep
from src.shared.security import decode_token

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


@router.post(
    "/tasks/{task_id}/messages", response_model=MessageResponse, status_code=201
)
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
    result = await use_case.execute(
        task_id=task_id, sender_id=payload["sub"], content=body.content
    )
    # Push live to anyone watching this task's chat over WebSocket.
    await chat_hub.broadcast(
        task_id,
        {
            "id": result.id,
            "task_id": result.task_id,
            "sender_id": result.sender_id,
            "content": result.content,
            "is_read": result.is_read,
            "created_at": result.created_at.isoformat(),
        },
    )
    return result


@router.websocket("/tasks/{task_id}/ws")
async def task_chat_ws(
    websocket: WebSocket, task_id: str, token: str | None = None
) -> None:
    """Live chat channel for a task. Listen-only: clients receive messages here
    and send them over the REST endpoint (which broadcasts to this hub).

    Auth is via a ``?token=`` query param because browsers can't set headers on
    a WebSocket handshake. Only the task's client and assigned hiver may connect.
    """
    if not token:
        await websocket.close(code=4401)
        return
    try:
        payload = decode_token(token)
    except AppError:
        await websocket.close(code=4401)
        return

    user_id = str(payload.get("sub", ""))
    async with AsyncSessionLocal() as session:
        task = await PostgresTaskRepository(session).find_by_id(task_id)
    if (
        task is None
        or task.hiver_id is None
        or user_id not in (task.client_id, task.hiver_id)
    ):
        await websocket.close(code=4403)
        return

    await chat_hub.connect(task_id, websocket)
    try:
        # Block until the client disconnects; inbound frames are ignored.
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        chat_hub.disconnect(task_id, websocket)
