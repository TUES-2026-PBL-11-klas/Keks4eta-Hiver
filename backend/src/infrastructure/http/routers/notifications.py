from fastapi import APIRouter, Query

from src.infrastructure.http.dependencies import SessionDep, UserPayloadDep
from src.infrastructure.database.repositories.notification_repository import (
    PostgresNotificationRepository,
)
from src.application.use_cases.notifications.notification_use_cases import (
    ListNotificationsUseCase,
    CountUnreadUseCase,
    MarkNotificationReadUseCase,
    MarkAllNotificationsReadUseCase,
)
from src.application.dtos.notification_dtos import (
    NotificationResponse,
    UnreadCountResponse,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
async def list_notifications(
    session: SessionDep,
    payload: UserPayloadDep,
    only_unread: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
) -> list[NotificationResponse]:
    use_case = ListNotificationsUseCase(PostgresNotificationRepository(session))
    return await use_case.execute(
        user_id=payload["sub"], only_unread=only_unread, limit=limit
    )


@router.get("/unread_count", response_model=UnreadCountResponse)
async def unread_count(
    session: SessionDep,
    payload: UserPayloadDep,
) -> UnreadCountResponse:
    use_case = CountUnreadUseCase(PostgresNotificationRepository(session))
    return UnreadCountResponse(unread=await use_case.execute(user_id=payload["sub"]))


@router.post("/read-all", status_code=200)
async def mark_all_read(
    session: SessionDep,
    payload: UserPayloadDep,
) -> dict:
    use_case = MarkAllNotificationsReadUseCase(PostgresNotificationRepository(session))
    return {"marked": await use_case.execute(user_id=payload["sub"])}


@router.post("/{notification_id}/read", status_code=200)
async def mark_read(
    notification_id: str,
    session: SessionDep,
    payload: UserPayloadDep,
) -> dict:
    use_case = MarkNotificationReadUseCase(PostgresNotificationRepository(session))
    ok = await use_case.execute(notification_id=notification_id, user_id=payload["sub"])
    return {"ok": ok}
