"""Unit tests for CreateOfferUseCase — the self-offer guard added with unified
accounts (a user is both client and hiver, but must not offer on their own task).
"""
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

import pytest  # noqa: E402

from src.application.dtos.offer_dtos import CreateOfferRequest  # noqa: E402
from src.application.use_cases.offers.create_offer_use_case import (  # noqa: E402
    CreateOfferUseCase,
)
from src.domain.entities.task import Task  # noqa: E402
from src.domain.errors.domain_errors import CannotOfferOnOwnTaskError  # noqa: E402


class FakeTaskRepo:
    def __init__(self, task: Task) -> None:
        self._task = task

    async def find_by_id(self, task_id: str):
        return self._task if self._task.id == task_id else None


class FakeOfferRepo:
    def __init__(self) -> None:
        self.saved: list = []

    async def find_by_task_and_hiver(self, task_id, hiver_id):
        return None

    async def save(self, offer):
        self.saved.append(offer)
        return offer


class FakeHiverRepo:
    async def find_by_id(self, hiver_id):
        return object()  # not reached for the self-offer case


def make_task(client_id="owner-1") -> Task:
    return Task(
        id="t1", client_id=client_id, vertical="care",
        subcategory="dog walking", title="Walk my dog", description="Twice a day",
    )


class TestSelfOfferGuard:
    async def test_cannot_offer_on_own_task(self):
        offer_repo = FakeOfferRepo()
        use_case = CreateOfferUseCase(
            task_repo=FakeTaskRepo(make_task(client_id="owner-1")),
            offer_repo=offer_repo,
            hiver_repo=FakeHiverRepo(),
        )
        with pytest.raises(CannotOfferOnOwnTaskError):
            await use_case.execute(
                CreateOfferRequest(price=50, message="I'll do it", estimated_hours=2),
                task_id="t1",
                hiver_id="owner-1",  # same as task.client_id
            )
        assert offer_repo.saved == []  # nothing persisted
