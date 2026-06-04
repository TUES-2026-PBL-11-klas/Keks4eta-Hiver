import uuid

from src.application.dtos.message_dtos import ConversationResponse, MessageResponse
from src.domain.entities.message import Message
from src.domain.entities.task import Task
from src.domain.errors.domain_errors import TaskNotFoundError, UnauthorizedActionError
from src.domain.interfaces.repositories import (
    IClientRepository,
    IMessageRepository,
    ITaskRepository,
)
from src.domain.services.event_bus import EventBus, notify


def _assert_participant(task: Task, user_id: str) -> str:
    """
    Chat is private to the task's client and the assigned hiver, and only exists
    once a hiver is assigned. Returns the *other* participant's id (the recipient).
    """
    if task.hiver_id is None:
        raise UnauthorizedActionError("message on a task with no assigned hiver")
    if user_id == task.client_id:
        return task.hiver_id
    if user_id == task.hiver_id:
        return task.client_id
    raise UnauthorizedActionError("access this conversation")


class SendMessageUseCase:
    def __init__(
        self,
        task_repo: ITaskRepository,
        message_repo: IMessageRepository,
        event_bus: EventBus | None = None,
    ) -> None:
        self._task_repo = task_repo
        self._message_repo = message_repo
        self._event_bus = event_bus

    async def execute(self, task_id: str, sender_id: str, content: str) -> MessageResponse:
        task = await self._task_repo.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        recipient_id = _assert_participant(task, sender_id)

        message = await self._message_repo.add(
            Message(id=str(uuid.uuid4()), task_id=task_id, sender_id=sender_id, content=content)
        )

        preview = content if len(content) <= 80 else content[:77] + "…"
        await notify(
            self._event_bus,
            recipient_id,
            "New message",
            f"On '{task.title}': {preview}",
            {"task_id": task_id},
        )

        return MessageResponse(
            id=message.id,
            task_id=message.task_id,
            sender_id=message.sender_id,
            content=message.content,
            is_read=message.is_read,
            created_at=message.created_at,
        )


class ListMessagesUseCase:
    def __init__(
        self,
        task_repo: ITaskRepository,
        message_repo: IMessageRepository,
    ) -> None:
        self._task_repo = task_repo
        self._message_repo = message_repo

    async def execute(self, task_id: str, reader_id: str) -> list[MessageResponse]:
        task = await self._task_repo.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        _assert_participant(task, reader_id)

        # Opening the thread marks the other party's messages as read.
        await self._message_repo.mark_read_for_reader(task_id, reader_id)

        messages = await self._message_repo.list_for_task(task_id)
        return [
            MessageResponse(
                id=m.id,
                task_id=m.task_id,
                sender_id=m.sender_id,
                content=m.content,
                is_read=m.is_read,
                created_at=m.created_at,
            )
            for m in messages
        ]


class ListConversationsUseCase:
    """Inbox: every task thread the user is in, newest-active first, each with
    the other party and an unread count. Resolves the message-only aggregate
    rows from the repo against the task and the other participant's profile."""

    def __init__(
        self,
        message_repo: IMessageRepository,
        task_repo: ITaskRepository,
        client_repo: IClientRepository,
    ) -> None:
        self._message_repo = message_repo
        self._task_repo = task_repo
        self._client_repo = client_repo

    async def execute(self, user_id: str) -> list[ConversationResponse]:
        rows = await self._message_repo.list_conversations(user_id)
        out: list[ConversationResponse] = []
        for row in rows:
            task = await self._task_repo.find_by_id(row.task_id)
            if task is None:
                continue
            other_id = (
                task.hiver_id if user_id == task.client_id else task.client_id
            )
            # Every account has a client facet (unified accounts), so this reads
            # the shared user row (name + avatar) for whoever the other party is.
            other = (
                await self._client_repo.find_by_id(other_id) if other_id else None
            )
            out.append(
                ConversationResponse(
                    task_id=row.task_id,
                    task_title=task.title,
                    other_user_id=other_id,
                    other_user_name=other.full_name if other else "Unknown",
                    other_user_avatar=other.avatar_url if other else None,
                    last_message=row.last_content,
                    last_at=row.last_at,
                    unread=row.unread,
                )
            )
        return out
