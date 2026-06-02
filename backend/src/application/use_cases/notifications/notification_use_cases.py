from src.domain.interfaces.repositories import INotificationRepository
from src.application.dtos.notification_dtos import NotificationResponse


class ListNotificationsUseCase:
    """Return a user's notification feed, newest first."""

    def __init__(self, repo: INotificationRepository) -> None:
        self._repo = repo

    async def execute(
        self, user_id: str, only_unread: bool = False, limit: int = 50
    ) -> list[NotificationResponse]:
        items = await self._repo.list_for_user(user_id, only_unread=only_unread, limit=limit)
        return [
            NotificationResponse(
                id=n.id,
                title=n.title,
                body=n.body,
                data=n.data,
                is_read=n.is_read,
                sent_at=n.sent_at,
            )
            for n in items
        ]


class CountUnreadUseCase:
    def __init__(self, repo: INotificationRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: str) -> int:
        return await self._repo.count_unread(user_id)


class MarkNotificationReadUseCase:
    def __init__(self, repo: INotificationRepository) -> None:
        self._repo = repo

    async def execute(self, notification_id: str, user_id: str) -> bool:
        return await self._repo.mark_read(notification_id, user_id)


class MarkAllNotificationsReadUseCase:
    def __init__(self, repo: INotificationRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: str) -> int:
        return await self._repo.mark_all_read(user_id)
