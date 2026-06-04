from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.interfaces.ports import INotificationPort, NotificationPayload
from src.infrastructure.database.models import NotificationLogModel


class InAppNotificationAdapter(INotificationPort):
    """
    The "push provider" for the in-app bell — persists notifications to the
    notification_log table. Implements the same INotificationPort an FCM/APNs
    adapter would, so swapping to real push later is a DI change only.
    Session-bound, so a notification lands in the same transaction as the action
    that triggered it (no orphan notifications if the action rolls back).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def send(self, payload: NotificationPayload) -> None:
        self._session.add(
            NotificationLogModel(
                user_id=payload.recipient_id,
                title=payload.title,
                body=payload.body,
                data=payload.data or {},
                is_read=False,
            )
        )
        await self._session.flush()

    async def send_bulk(self, payloads: list[NotificationPayload]) -> list[bool]:
        for payload in payloads:
            await self.send(payload)
        return [True] * len(payloads)
