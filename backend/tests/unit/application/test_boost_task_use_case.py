"""Unit tests for the Phase 5 task-boost use case."""

import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://t:t@localhost/t")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_dummy")

import pytest

from src.application.use_cases.tasks.boost_task_use_case import BoostTaskUseCase
from src.domain.entities.task import Task
from src.domain.errors.domain_errors import (
    TaskNotFoundError,
    UnauthorizedActionError,
)
from src.domain.value_objects.money import Money


class FakeTaskRepo:
    def __init__(self, tasks: list[Task] | None = None) -> None:
        self.tasks = {t.id: t for t in (tasks or [])}
        self.saved: Task | None = None

    async def find_by_id(self, task_id: str) -> Task | None:
        return self.tasks.get(task_id)

    async def save(self, task: Task) -> Task:
        self.saved = task
        self.tasks[task.id] = task
        return task


class FakePaymentPort:
    def __init__(self) -> None:
        self.held: list[tuple[float, str]] = []

    async def hold_payment(self, amount: Money, customer_id: str) -> str:
        self.held.append((float(amount.value), customer_id))
        return "pi_mock"

    async def release_payment(self, pi: str) -> None: ...
    async def refund_payment(self, pi: str, amount: Money) -> None: ...
    async def create_customer(self, email: str, name: str) -> str:
        return "cus_mock"


def make_task(tid: str = "t1", client_id: str = "c1") -> Task:
    return Task(
        id=tid,
        client_id=client_id,
        vertical="home",
        subcategory="cleaning",
        title="Test",
        description="x",
    )


class TestBoostTaskUseCase:
    async def test_owner_boosts_task(self):
        task = make_task()
        repo = FakeTaskRepo([task])
        payment = FakePaymentPort()
        result = await BoostTaskUseCase(repo, payment).execute("t1", "c1")

        assert result.task_id == "t1"
        assert result.featured_until is not None
        assert task.is_featured() is True
        assert repo.saved is task
        assert payment.held and payment.held[0][1] == "c1"

    async def test_non_owner_cannot_boost(self):
        repo = FakeTaskRepo([make_task()])
        with pytest.raises(UnauthorizedActionError):
            await BoostTaskUseCase(repo, FakePaymentPort()).execute("t1", "intruder")

    async def test_missing_task_raises(self):
        with pytest.raises(TaskNotFoundError):
            await BoostTaskUseCase(FakeTaskRepo(), FakePaymentPort()).execute(
                "nope", "c1"
            )

    async def test_not_charged_when_unauthorized(self):
        repo = FakeTaskRepo([make_task()])
        payment = FakePaymentPort()
        with pytest.raises(UnauthorizedActionError):
            await BoostTaskUseCase(repo, payment).execute("t1", "intruder")
        assert payment.held == []  # ownership checked before charging
