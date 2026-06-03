from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass


@dataclass
class DomainEvent:
    event_type: str
    payload: dict


Handler = Callable[[DomainEvent], Awaitable[None]]


class EventBus:
    """
    Observer Pattern: publishers emit events, observers react.
    OOP: Decouples event producers from consumers.

    Why: TaskAccepted triggers escrow hold, notification, and chat creation.
    Without Observer, CreateTaskUseCase would import all three services directly.
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = {}

    def subscribe(self, event_type: str, handler: Handler) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def publish(self, event: DomainEvent) -> None:
        for handler in self._handlers.get(event.event_type, []):
            await handler(event)

    def clear(self, event_type: str | None = None) -> None:
        if event_type:
            self._handlers.pop(event_type, None)
        else:
            self._handlers.clear()


NOTIFY_EVENT = "notify"


async def notify(
    bus: EventBus | None,
    recipient_id: str,
    title: str,
    body: str,
    data: dict | None = None,
) -> None:
    """
    Convenience for use cases: emit a notification event if a bus is wired.
    Optional by design — unit tests construct use cases without a bus and these
    calls become no-ops, while the HTTP layer injects a request-scoped bus whose
    subscriber persists the notification (Observer pattern).
    """
    if bus is None:
        return
    await bus.publish(
        DomainEvent(
            event_type=NOTIFY_EVENT,
            payload={
                "recipient_id": recipient_id,
                "title": title,
                "body": body,
                "data": data or {},
            },
        )
    )
