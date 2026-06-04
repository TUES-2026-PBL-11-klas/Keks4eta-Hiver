from collections.abc import AsyncGenerator
from typing import Annotated, Any

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import Client, Hiver
from src.domain.errors.domain_errors import InvalidTokenError, UnauthorizedActionError
from src.domain.interfaces.ports import NotificationPayload
from src.domain.services.event_bus import NOTIFY_EVENT, DomainEvent, EventBus
from src.infrastructure.database.repositories.user_repository import (
    PostgresClientRepository,
    PostgresHiverRepository,
)
from src.infrastructure.database.session import AsyncSessionLocal
from src.infrastructure.notifications.in_app_adapter import InAppNotificationAdapter
from src.shared.security import decode_token


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session, session.begin():
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user_payload(
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise InvalidTokenError()
    token = authorization.removeprefix("Bearer ")
    return decode_token(token)


UserPayloadDep = Annotated[dict[str, Any], Depends(get_current_user_payload)]


async def get_current_client(
    payload: UserPayloadDep,
    session: SessionDep,
) -> Client:
    if payload.get("role") != "client":
        raise UnauthorizedActionError("access client-only resource")
    client = await PostgresClientRepository(session).find_by_id(payload["sub"])
    if client is None:
        raise UnauthorizedActionError("access this resource")
    return client


async def get_current_hiver(
    payload: UserPayloadDep,
    session: SessionDep,
) -> Hiver:
    if payload.get("role") != "hiver":
        raise UnauthorizedActionError("access hiver-only resource")
    hiver = await PostgresHiverRepository(session).find_by_id(payload["sub"])
    if hiver is None:
        raise UnauthorizedActionError("access this resource")
    return hiver


ClientDep = Annotated[Client, Depends(get_current_client)]
HiverDep = Annotated[Hiver, Depends(get_current_hiver)]


async def get_event_bus(session: SessionDep) -> EventBus:
    """
    Request-scoped EventBus with the in-app notification subscriber attached.
    The subscriber is bound to *this request's* session, so a notification is
    written in the same transaction as the action that emitted it (Observer
    pattern: use cases publish, this handler persists — neither knows the other).
    """
    bus = EventBus()
    adapter = InAppNotificationAdapter(session)

    async def _on_notify(event: DomainEvent) -> None:
        p = event.payload
        await adapter.send(
            NotificationPayload(
                recipient_id=p["recipient_id"],
                title=p["title"],
                body=p["body"],
                data=p.get("data", {}),
            )
        )

    bus.subscribe(NOTIFY_EVENT, _on_notify)
    return bus


EventBusDep = Annotated[EventBus, Depends(get_event_bus)]
