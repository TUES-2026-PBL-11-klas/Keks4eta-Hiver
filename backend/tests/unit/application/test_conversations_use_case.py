"""Unit tests for the Phase 6 inbox (ListConversationsUseCase)."""

import os
import sys
from datetime import UTC, datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://t:t@localhost/t")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_dummy")

from src.application.use_cases.messages.message_use_cases import (
    ListConversationsUseCase,
)
from src.domain.entities.task import Task
from src.domain.entities.user import Client
from src.domain.interfaces.repositories import ConversationRow


class FakeMessageRepo:
    def __init__(self, rows: list[ConversationRow]) -> None:
        self.rows = rows

    async def list_conversations(self, user_id: str) -> list[ConversationRow]:
        return self.rows


class FakeTaskRepo:
    def __init__(self, tasks: list[Task]) -> None:
        self.tasks = {t.id: t for t in tasks}

    async def find_by_id(self, task_id: str) -> Task | None:
        return self.tasks.get(task_id)


class FakeClientRepo:
    def __init__(self, clients: list[Client]) -> None:
        self.clients = {c.id: c for c in clients}

    async def find_by_id(self, client_id: str) -> Client | None:
        return self.clients.get(client_id)


def make_task(tid: str, client_id: str, hiver_id: str) -> Task:
    return Task(
        id=tid,
        client_id=client_id,
        hiver_id=hiver_id,
        vertical="home",
        subcategory="cleaning",
        title=f"Task {tid}",
        description="x",
    )


def make_client(cid: str, name: str) -> Client:
    return Client(id=cid, email=f"{cid}@t.com", _password_hash=None, full_name=name)


def row(task_id: str, unread: int = 0) -> ConversationRow:
    return ConversationRow(
        task_id=task_id, last_content="hello", last_at=datetime.now(UTC), unread=unread
    )


class TestListConversationsUseCase:
    async def test_other_party_is_hiver_when_user_is_client(self):
        uc = ListConversationsUseCase(
            FakeMessageRepo([row("t1", unread=2)]),
            FakeTaskRepo([make_task("t1", client_id="me", hiver_id="h1")]),
            FakeClientRepo([make_client("h1", "Hiver One")]),
        )
        convs = await uc.execute("me")
        assert len(convs) == 1
        assert convs[0].task_title == "Task t1"
        assert convs[0].other_user_id == "h1"
        assert convs[0].other_user_name == "Hiver One"
        assert convs[0].unread == 2

    async def test_other_party_is_client_when_user_is_hiver(self):
        uc = ListConversationsUseCase(
            FakeMessageRepo([row("t1")]),
            FakeTaskRepo([make_task("t1", client_id="c1", hiver_id="me")]),
            FakeClientRepo([make_client("c1", "Client One")]),
        )
        convs = await uc.execute("me")
        assert convs[0].other_user_id == "c1"
        assert convs[0].other_user_name == "Client One"

    async def test_skips_conversation_whose_task_is_gone(self):
        uc = ListConversationsUseCase(
            FakeMessageRepo([row("ghost")]),
            FakeTaskRepo([]),
            FakeClientRepo([]),
        )
        assert await uc.execute("me") == []

    async def test_unknown_other_party_falls_back(self):
        uc = ListConversationsUseCase(
            FakeMessageRepo([row("t1")]),
            FakeTaskRepo([make_task("t1", client_id="me", hiver_id="h1")]),
            FakeClientRepo([]),  # other party profile not found
        )
        convs = await uc.execute("me")
        assert convs[0].other_user_name == "Unknown"
