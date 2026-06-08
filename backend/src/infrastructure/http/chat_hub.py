from __future__ import annotations

from collections import defaultdict

from fastapi import WebSocket


class ChatHub:
    """In-memory fan-out of task-chat messages to connected WebSockets.

    Each task id is a "room"; sending happens over REST (validated, rate-limit
    friendly) and the REST handler calls :meth:`broadcast` so every open socket
    on that task gets the message live. Single-instance only — for a multi-replica
    deploy put Redis pub/sub behind this same tiny interface.
    """

    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, task_id: str, ws: WebSocket) -> None:
        await ws.accept()
        self._rooms[task_id].add(ws)

    def disconnect(self, task_id: str, ws: WebSocket) -> None:
        room = self._rooms.get(task_id)
        if room is not None:
            room.discard(ws)
            if not room:
                self._rooms.pop(task_id, None)

    async def broadcast(self, task_id: str, message: dict[str, object]) -> None:
        # Iterate a copy: a failed send means a dead socket, which we prune.
        for ws in list(self._rooms.get(task_id, set())):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(task_id, ws)


# Module-level singleton shared by the REST send handler and the WS endpoint.
chat_hub = ChatHub()
