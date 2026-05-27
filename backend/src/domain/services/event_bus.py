from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Awaitable


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
