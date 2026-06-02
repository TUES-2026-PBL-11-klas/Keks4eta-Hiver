from __future__ import annotations
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.notification import Notification
from src.domain.interfaces.repositories import INotificationRepository
from src.infrastructure.database.models import NotificationLogModel


def _to_domain(m: NotificationLogModel) -> Notification:
    return Notification(
        id=m.id,
        user_id=m.user_id,
        title=m.title,
        body=m.body,
        data=m.data or {},
        is_read=m.is_read,
        sent_at=m.sent_at,
    )


class PostgresNotificationRepository(INotificationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_user(
        self, user_id: str, only_unread: bool = False, limit: int = 50
    ) -> list[Notification]:
        stmt = select(NotificationLogModel).where(NotificationLogModel.user_id == user_id)
        if only_unread:
            stmt = stmt.where(NotificationLogModel.is_read.is_(False))
        stmt = stmt.order_by(NotificationLogModel.sent_at.desc()).limit(limit)
        result = await self._session.execute(stmt)
        return [_to_domain(m) for m in result.scalars()]

    async def count_unread(self, user_id: str) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(NotificationLogModel)
            .where(
                NotificationLogModel.user_id == user_id,
                NotificationLogModel.is_read.is_(False),
            )
        )
        return int(result.scalar() or 0)

    async def mark_read(self, notification_id: str, user_id: str) -> bool:
        result = await self._session.execute(
            update(NotificationLogModel)
            .where(
                NotificationLogModel.id == notification_id,
                NotificationLogModel.user_id == user_id,
            )
            .values(is_read=True)
        )
        await self._session.flush()
        return result.rowcount > 0

    async def mark_all_read(self, user_id: str) -> int:
        result = await self._session.execute(
            update(NotificationLogModel)
            .where(
                NotificationLogModel.user_id == user_id,
                NotificationLogModel.is_read.is_(False),
            )
            .values(is_read=True)
        )
        await self._session.flush()
        return result.rowcount
