from __future__ import annotations

import uuid
from typing import cast

from sqlalchemy import select, text, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.message import Message
from src.domain.interfaces.repositories import ConversationRow, IMessageRepository
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
        result = cast(
            CursorResult[None],
            await self._session.execute(
                update(MessageModel)
                .where(
                    MessageModel.task_id == task_id,
                    MessageModel.sender_id != reader_id,
                    MessageModel.is_read.is_(False),
                )
                .values(is_read=True)
            ),
        )
        await self._session.flush()
        return result.rowcount

    async def list_conversations(self, user_id: str) -> list[ConversationRow]:
        # One row per task the user participates in (client or assigned hiver):
        # the latest message (via ROW_NUMBER) plus a count of messages still
        # unread by this user. Newest-active conversation first.
        rows = await self._session.execute(
            text(
                """
                WITH my_tasks AS (
                    -- A chat exists once a hiver is assigned; show every such task
                    -- even before the first message so it's reachable from the inbox.
                    SELECT id, updated_at FROM tasks
                    WHERE (client_id = :uid OR hiver_id = :uid)
                      AND hiver_id IS NOT NULL
                ),
                latest AS (
                    SELECT m.task_id, m.content, m.created_at,
                           ROW_NUMBER() OVER (
                               PARTITION BY m.task_id ORDER BY m.created_at DESC
                           ) AS rn
                    FROM messages m
                    WHERE m.task_id IN (SELECT id FROM my_tasks)
                )
                SELECT t.id AS task_id,
                       COALESCE(l.content, '') AS last_content,
                       COALESCE(l.created_at, t.updated_at) AS last_at,
                       (SELECT COUNT(*) FROM messages m2
                        WHERE m2.task_id = t.id
                          AND m2.sender_id <> :uid
                          AND m2.is_read = false) AS unread
                FROM my_tasks t
                LEFT JOIN latest l ON l.task_id = t.id AND l.rn = 1
                ORDER BY last_at DESC
                """
            ),
            {"uid": user_id},
        )
        return [
            ConversationRow(
                task_id=r.task_id,
                last_content=r.last_content,
                last_at=r.last_at,
                unread=int(r.unread),
            )
            for r in rows
        ]
