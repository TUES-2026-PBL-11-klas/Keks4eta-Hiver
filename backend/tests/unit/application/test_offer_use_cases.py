"""Unit tests for offer use cases."""
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

from src.application.dtos.offer_dtos import CreateOfferRequest
from src.application.use_cases.offers.accept_offer_use_case import AcceptOfferUseCase
from src.application.use_cases.offers.create_offer_use_case import CreateOfferUseCase
from src.domain.entities.offer import Offer
from src.domain.entities.task import Task
from src.domain.entities.user import Hiver
from src.domain.errors.domain_errors import (
    HiverNotFoundError,
    OfferAlreadyExistsError,
    OfferNotFoundError,
    TaskAlreadyAcceptedError,
    TaskNotFoundError,
    UnauthorizedActionError,
)
from src.domain.value_objects.money import Money
from src.domain.value_objects.rating import Rating


def make_task(tid: str = "t-1", client_id: str = "c-1") -> Task:
    return Task(
        id=tid, client_id=client_id, vertical="home", subcategory="cleaning",
        title="Clean house", description="Need cleaning",
    )


def make_hiver(hid: str = "h-1") -> Hiver:
    return Hiver(id=hid, email=f"{hid}@x.com", _password_hash=None, full_name="H",
                 avg_rating=Rating(4.5))


def make_offer(oid: str = "o-1", task_id: str = "t-1", hiver_id: str = "h-1") -> Offer:
    return Offer(
        id=oid, task_id=task_id, hiver_id=hiver_id,
        price=Money.of(100), message="Can help", estimated_hours=2.0,
    )


class FakeTaskRepo:
    def __init__(self, tasks: list | None = None) -> None:
        self.saved: list = tasks or []

    async def find_by_id(self, tid: str):
        return next((t for t in self.saved if t.id == tid), None)

    async def save(self, task):
        for i, t in enumerate(self.saved):
            if t.id == task.id:
                self.saved[i] = task
                return task
        self.saved.append(task)
        return task


class FakeOfferRepo:
    def __init__(self, offers: list | None = None) -> None:
        self.saved: list = offers or []

    async def find_by_id(self, oid: str):
        return next((o for o in self.saved if o.id == oid), None)

    async def find_by_task(self, task_id: str):
        return [o for o in self.saved if o.task_id == task_id]

    async def find_by_task_and_hiver(self, task_id: str, hiver_id: str):
        return next(
            (o for o in self.saved if o.task_id == task_id and o.hiver_id == hiver_id), None
        )

    async def save(self, offer):
        for i, o in enumerate(self.saved):
            if o.id == offer.id:
                self.saved[i] = offer
                return offer
        self.saved.append(offer)
        return offer


class FakeHiverRepo:
    def __init__(self, hivers: list | None = None) -> None:
        self.saved: list = hivers or []

    async def find_by_id(self, hid: str):
        return next((h for h in self.saved if h.id == hid), None)


class FakeTransactionRepo:
    def __init__(self) -> None:
        self.saved: list = []

    async def find_by_task(self, task_id: str):
        return next((t for t in self.saved if t.task_id == task_id), None)

    async def save(self, txn):
        self.saved.append(txn)
        return txn


class FakePaymentPort:
    async def hold_payment(self, amount, customer_id: str) -> str:
        return "pi_mock_123"

    async def release_payment(self, payment_intent_id: str) -> None:
        pass

    async def refund_payment(self, payment_intent_id: str, amount) -> None:
        pass

    async def create_customer(self, email: str, name: str) -> str:
        return "cus_mock_123"


class TestCreateOfferUseCase:
    async def test_creates_offer_successfully(self):
        task = make_task()
        hiver = make_hiver()
        task_repo = FakeTaskRepo([task])
        offer_repo = FakeOfferRepo()
        hiver_repo = FakeHiverRepo([hiver])

        resp = await CreateOfferUseCase(task_repo, offer_repo, hiver_repo).execute(
            CreateOfferRequest(price=100.0, message="Can do it", estimated_hours=2.0),
            task_id="t-1", hiver_id="h-1",
        )
        assert resp.task_id == "t-1"
        assert resp.hiver_id == "h-1"
        assert len(offer_repo.saved) == 1

    async def test_task_not_found_raises(self):
        with pytest.raises(TaskNotFoundError):
            await CreateOfferUseCase(FakeTaskRepo(), FakeOfferRepo(), FakeHiverRepo()).execute(
                CreateOfferRequest(price=100.0, message="x", estimated_hours=1.0),
                task_id="nope", hiver_id="h-1",
            )

    async def test_task_not_open_raises(self):
        task = make_task()
        task.accept("h-1")
        with pytest.raises(TaskAlreadyAcceptedError):
            await CreateOfferUseCase(
                FakeTaskRepo([task]), FakeOfferRepo(), FakeHiverRepo([make_hiver()])
            ).execute(
                CreateOfferRequest(price=100.0, message="x", estimated_hours=1.0),
                task_id="t-1", hiver_id="h-1",
            )

    async def test_hiver_not_found_raises(self):
        task = make_task()
        with pytest.raises(HiverNotFoundError):
            await CreateOfferUseCase(FakeTaskRepo([task]), FakeOfferRepo(), FakeHiverRepo()).execute(
                CreateOfferRequest(price=100.0, message="x", estimated_hours=1.0),
                task_id="t-1", hiver_id="h-missing",
            )

    async def test_duplicate_offer_raises(self):
        task = make_task()
        hiver = make_hiver()
        existing = make_offer()
        with pytest.raises(OfferAlreadyExistsError):
            await CreateOfferUseCase(
                FakeTaskRepo([task]), FakeOfferRepo([existing]), FakeHiverRepo([hiver])
            ).execute(
                CreateOfferRequest(price=100.0, message="x", estimated_hours=1.0),
                task_id="t-1", hiver_id="h-1",
            )


class TestAcceptOfferUseCase:
    async def test_accepts_offer_and_creates_escrow(self):
        task = make_task()
        offer = make_offer()
        task_repo = FakeTaskRepo([task])
        offer_repo = FakeOfferRepo([offer])
        txn_repo = FakeTransactionRepo()
        payment = FakePaymentPort()

        resp = await AcceptOfferUseCase(task_repo, offer_repo, txn_repo, payment).execute(
            task_id="t-1", offer_id="o-1", client_id="c-1"
        )
        assert resp.status == "accepted"
        assert len(txn_repo.saved) == 1

    async def test_task_not_found_raises(self):
        with pytest.raises(TaskNotFoundError):
            await AcceptOfferUseCase(
                FakeTaskRepo(), FakeOfferRepo(), FakeTransactionRepo(), FakePaymentPort()
            ).execute(task_id="nope", offer_id="o-1", client_id="c-1")

    async def test_unauthorized_raises(self):
        task = make_task(client_id="c-1")
        offer = make_offer()
        with pytest.raises(UnauthorizedActionError):
            await AcceptOfferUseCase(
                FakeTaskRepo([task]), FakeOfferRepo([offer]),
                FakeTransactionRepo(), FakePaymentPort()
            ).execute(task_id="t-1", offer_id="o-1", client_id="not-owner")

    async def test_offer_not_found_raises(self):
        task = make_task()
        with pytest.raises(OfferNotFoundError):
            await AcceptOfferUseCase(
                FakeTaskRepo([task]), FakeOfferRepo(),
                FakeTransactionRepo(), FakePaymentPort()
            ).execute(task_id="t-1", offer_id="missing", client_id="c-1")

    async def test_rejects_other_pending_offers(self):
        task = make_task()
        offer1 = make_offer("o-1")
        offer2 = make_offer("o-2", hiver_id="h-2")
        task_repo = FakeTaskRepo([task])
        offer_repo = FakeOfferRepo([offer1, offer2])

        await AcceptOfferUseCase(task_repo, offer_repo, FakeTransactionRepo(), FakePaymentPort()
                                 ).execute(task_id="t-1", offer_id="o-1", client_id="c-1")

        assert offer1.status.value == "accepted"
        assert offer2.status.value == "rejected"
