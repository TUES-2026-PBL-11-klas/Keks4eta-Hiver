from __future__ import annotations
import asyncio
from typing import Callable, Awaitable, TypeVar

T = TypeVar("T")


class BroadcastSemaphore:
    """
    OOP: Encapsulates rate-limiting logic for urgent task broadcasts.
    Prevents overwhelming Firebase FCM with too many simultaneous requests.
    Concurrency: async semaphore controls concurrent access to a shared resource.
    """

    def __init__(self, max_concurrent: int = 10) -> None:
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def broadcast(
        self,
        send_fn: Callable[[T], Awaitable],
        recipients: list[T],
    ) -> list:
        """Send to all recipients, at most max_concurrent at a time."""
        async def _send_one(recipient: T):
            async with self._semaphore:
                return await send_fn(recipient)

        return await asyncio.gather(
            *[_send_one(r) for r in recipients],
            return_exceptions=True,  # don't fail all if one fails
        )
