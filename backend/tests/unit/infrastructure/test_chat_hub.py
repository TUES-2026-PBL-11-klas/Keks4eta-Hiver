"""Unit tests for the in-memory WebSocket ChatHub."""

import importlib
import sys
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[3]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

ChatHub = importlib.import_module("src.infrastructure.http.chat_hub").ChatHub


class FakeWS:
    def __init__(self, fail: bool = False) -> None:
        self.accepted = False
        self.sent: list[dict[str, object]] = []
        self._fail = fail

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, data: dict[str, object]) -> None:
        if self._fail:
            raise RuntimeError("socket closed")
        self.sent.append(data)


class TestChatHub:
    async def test_connect_accepts_and_registers(self) -> None:
        hub = ChatHub()
        ws: Any = FakeWS()
        await hub.connect("t1", ws)
        assert ws.accepted is True
        await hub.broadcast("t1", {"x": 1})
        assert ws.sent == [{"x": 1}]

    async def test_broadcast_reaches_all_in_room_only(self) -> None:
        hub = ChatHub()
        a: Any = FakeWS()
        b: Any = FakeWS()
        other: Any = FakeWS()
        await hub.connect("t1", a)
        await hub.connect("t1", b)
        await hub.connect("t2", other)
        await hub.broadcast("t1", {"m": "hi"})
        assert a.sent and b.sent
        assert other.sent == []  # different room

    async def test_disconnect_stops_delivery(self) -> None:
        hub = ChatHub()
        ws: Any = FakeWS()
        await hub.connect("t1", ws)
        hub.disconnect("t1", ws)
        await hub.broadcast("t1", {"m": 1})
        assert ws.sent == []

    async def test_failed_socket_is_pruned(self) -> None:
        hub = ChatHub()
        good: Any = FakeWS()
        bad: Any = FakeWS(fail=True)
        await hub.connect("t1", good)
        await hub.connect("t1", bad)
        await hub.broadcast("t1", {"m": 1})
        assert good.sent == [{"m": 1}]
        # The failing socket was removed, so a second broadcast still works.
        await hub.broadcast("t1", {"m": 2})
        assert good.sent == [{"m": 1}, {"m": 2}]
