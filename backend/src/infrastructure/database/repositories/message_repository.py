from __future__ import annotations

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.message import Message
from src.domain.interfaces.repositories import IMessageRepository
from src.infrastructure.database.models import MessageModel


def _to_domain(m: MessageModel) -> Message:
    return Message(
        id=m.id,
        task_id=m.task_id,
        sender_id=m.sender_id,
        content=m.content,
        is_read=m.is_read,
        created_at=m.created_at,
    )


class PostgresMessageRepository(IMessageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, message: Message) -> Message:
        model = MessageModel(
            id=message.id or str(uuid.uuid4()),
            task_id=message.task_id,
            sender_id=message.sender_id,
            content=message.content,
            is_read=message.is_read,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_domain(model)

    async def list_for_task(self, task_id: str) -> list[Message]:
        result = await self._session.execute(
            select(MessageModel)
            .where(MessageModel.task_id == task_id)
            .order_by(MessageModel.created_at.asc())
        )
        return [_to_domain(m) for m in result.scalars()]

    async def mark_read_for_reader(self, task_id: str, reader_id: str) -> int:
        result = await self._session.execute(
            update(MessageModel)
            .where(
                MessageModel.task_id == task_id,
                MessageModel.sender_id != reader_id,
                MessageModel.is_read.is_(False),
            )
            .values(is_read=True)
        )
        await self._session.flush()
        return result.rowcount
