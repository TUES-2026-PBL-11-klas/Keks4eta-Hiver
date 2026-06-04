"""Unit tests for payment and review use cases."""
import os
import sys
from datetime import datetime
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

from src.application.dtos.review_dtos import SubmitReviewRequest
from src.application.use_cases.payments.get_escrow_use_case import GetEscrowUseCase
from src.application.use_cases.payments.release_escrow_use_case import ReleaseEscrowUseCase
from src.application.use_cases.reviews.list_reviews_use_case import (
    ListTaskReviewsUseCase,
    ListUserReviewsUseCase,
)
from src.application.use_cases.reviews.submit_review_use_case import SubmitReviewUseCase
from src.domain.entities.review import Review
from src.domain.entities.task import Task, TaskStatus
from src.domain.entities.transaction import Transaction
from src.domain.errors.domain_errors import (
    ReviewAlreadySubmittedError,
    TaskNotCompletedError,
    TaskNotFoundError,
    TransactionNotFoundError,
    UnauthorizedActionError,
)
from src.domain.value_objects.money import Money
from src.domain.value_objects.rating import Rating


def make_task(tid: str = "t-1", client_id: str = "c-1", hiver_id: str | None = "h-1") -> Task:
    task = Task(
        id=tid, client_id=client_id, vertical="home", subcategory="cleaning",
        title="Clean house", description="Needs cleaning",
    )
    if hiver_id:
        task.accept(hiver_id)
    return task


def make_completed_task() -> Task:
    task = make_task()
    task.start("h-1")
    task.complete("c-1")
    return task


def make_transaction(task_id: str = "t-1") -> Transaction:
    return Transaction.create_for_task(
        id="txn-1",
        task_id=task_id,
        client_id="c-1",
        hiver_id="h-1",
        offer_price=Money.of(100),
        stripe_payment_intent_id="pi_mock",
    )


def make_review(
    rid: str = "r-1",
    task_id: str = "t-1",
    reviewer_id: str = "c-1",
    reviewee_id: str = "h-1",
    is_revealed: bool = True,
) -> Review:
    return Review(
        id=rid, task_id=task_id, reviewer_id=reviewer_id, reviewee_id=reviewee_id,
        rating=Rating(4.5), comment="Great job", is_revealed=is_revealed,
        created_at=datetime.utcnow(),
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


class FakeTransactionRepo:
    def __init__(self, txns: list | None = None) -> None:
        self.saved: list = txns or []

    async def find_by_task(self, task_id: str):
        return next((t for t in self.saved if t.task_id == task_id), None)

    async def save(self, txn):
        for i, t in enumerate(self.saved):
            if t.id == txn.id:
                self.saved[i] = txn
                return txn
        self.saved.append(txn)
        return txn


class FakePaymentPort:
    def __init__(self) -> None:
        self.released: list = []
        self.refunded: list = []

    async def hold_payment(self, amount, customer_id: str) -> str:
        return "pi_mock"

    async def release_payment(self, payment_intent_id: str) -> None:
        self.released.append(payment_intent_id)

    async def refund_payment(self, payment_intent_id: str, amount) -> None:
        self.refunded.append(payment_intent_id)

    async def create_customer(self, email: str, name: str) -> str:
        return "cus_mock"


class FakeReviewRepo:
    def __init__(self, reviews: list | None = None) -> None:
        self.saved: list = reviews or []

    async def find_by_task(self, task_id: str):
        return [r for r in self.saved if r.task_id == task_id]

    async def find_by_reviewee(self, reviewee_id: str):
        return [r for r in self.saved if r.reviewee_id == reviewee_id]

    async def find_by_task_and_reviewer(self, task_id: str, reviewer_id: str):
        return next(
            (r for r in self.saved if r.task_id == task_id and r.reviewer_id == reviewer_id), None
        )

    async def save(self, review):
        self.saved.append(review)
        return review


# ── Release Escrow ─────────────────────────────────────────────────────────────


class TestReleaseEscrowUseCase:
    async def test_releases_from_completed_task(self):
        task = make_completed_task()
        txn = make_transaction()
        payment = FakePaymentPort()

        result = await ReleaseEscrowUseCase(
            FakeTaskRepo([task]), FakeTransactionRepo([txn]), payment
        ).execute("t-1", "c-1")

        assert result["status"] == "released"
        assert "pi_mock" in payment.released

    async def test_releases_from_in_progress_task(self):
        task = make_task()
        task.start("h-1")
        txn = make_transaction()
        payment = FakePaymentPort()

        result = await ReleaseEscrowUseCase(
            FakeTaskRepo([task]), FakeTransactionRepo([txn]), payment
        ).execute("t-1", "c-1")

        assert result["status"] == "released"
        assert task.status == TaskStatus.COMPLETED

    async def test_task_not_found_raises(self):
        with pytest.raises(TaskNotFoundError):
            await ReleaseEscrowUseCase(
                FakeTaskRepo(), FakeTransactionRepo(), FakePaymentPort()
            ).execute("nope", "c-1")

    async def test_unauthorized_raises(self):
        task = make_completed_task()
        txn = make_transaction()
        with pytest.raises(UnauthorizedActionError):
            await ReleaseEscrowUseCase(
                FakeTaskRepo([task]), FakeTransactionRepo([txn]), FakePaymentPort()
            ).execute("t-1", "not-owner")

    async def test_no_transaction_raises(self):
        task = make_completed_task()
        with pytest.raises(TransactionNotFoundError):
            await ReleaseEscrowUseCase(
                FakeTaskRepo([task]), FakeTransactionRepo(), FakePaymentPort()
            ).execute("t-1", "c-1")

    async def test_wrong_task_status_raises(self):
        task = make_task()  # only ACCEPTED, not in_progress or completed
        txn = make_transaction()
        with pytest.raises(TaskNotCompletedError):
            await ReleaseEscrowUseCase(
                FakeTaskRepo([task]), FakeTransactionRepo([txn]), FakePaymentPort()
            ).execute("t-1", "c-1")


# ── Get Escrow ─────────────────────────────────────────────────────────────────


class TestGetEscrowUseCase:
    async def test_returns_escrow_for_client(self):
        task = make_task()
        txn = make_transaction()
        result = await GetEscrowUseCase(FakeTaskRepo([task]), FakeTransactionRepo([txn])).execute(
            "t-1", "c-1"
        )
        assert result is not None
        assert result.task_id == "t-1"

    async def test_returns_none_when_no_escrow(self):
        task = make_task()
        result = await GetEscrowUseCase(FakeTaskRepo([task]), FakeTransactionRepo()).execute(
            "t-1", "c-1"
        )
        assert result is None

    async def test_returns_escrow_for_hiver(self):
        task = make_task()
        txn = make_transaction()
        result = await GetEscrowUseCase(FakeTaskRepo([task]), FakeTransactionRepo([txn])).execute(
            "t-1", "h-1"
        )
        assert result is not None

    async def test_task_not_found_raises(self):
        with pytest.raises(TaskNotFoundError):
            await GetEscrowUseCase(FakeTaskRepo(), FakeTransactionRepo()).execute("nope", "c-1")

    async def test_unauthorized_raises(self):
        task = make_task()
        with pytest.raises(UnauthorizedActionError):
            await GetEscrowUseCase(FakeTaskRepo([task]), FakeTransactionRepo()).execute(
                "t-1", "stranger"
            )


# ── Submit Review ──────────────────────────────────────────────────────────────


class TestSubmitReviewUseCase:
    async def test_client_submits_review(self):
        task = make_completed_task()
        review_repo = FakeReviewRepo()

        resp = await SubmitReviewUseCase(FakeTaskRepo([task]), review_repo).execute(
            "t-1", "c-1", SubmitReviewRequest(rating=4.5, comment="Good job")
        )
        assert resp.reviewer_id == "c-1"
        assert resp.reviewee_id == "h-1"
        assert len(review_repo.saved) == 1

    async def test_hiver_submits_review(self):
        task = make_completed_task()
        review_repo = FakeReviewRepo()

        resp = await SubmitReviewUseCase(FakeTaskRepo([task]), review_repo).execute(
            "t-1", "h-1", SubmitReviewRequest(rating=5.0, comment="Great client")
        )
        assert resp.reviewer_id == "h-1"
        assert resp.reviewee_id == "c-1"

    async def test_task_not_found_raises(self):
        with pytest.raises(TaskNotFoundError):
            await SubmitReviewUseCase(FakeTaskRepo(), FakeReviewRepo()).execute(
                "nope", "c-1", SubmitReviewRequest(rating=5.0, comment="x")
            )

    async def test_task_not_completed_raises(self):
        task = make_task()  # only ACCEPTED
        with pytest.raises(TaskNotCompletedError):
            await SubmitReviewUseCase(FakeTaskRepo([task]), FakeReviewRepo()).execute(
                "t-1", "c-1", SubmitReviewRequest(rating=5.0, comment="x")
            )

    async def test_stranger_raises(self):
        task = make_completed_task()
        with pytest.raises(UnauthorizedActionError):
            await SubmitReviewUseCase(FakeTaskRepo([task]), FakeReviewRepo()).execute(
                "t-1", "stranger", SubmitReviewRequest(rating=5.0, comment="x")
            )

    async def test_duplicate_review_raises(self):
        task = make_completed_task()
        existing = make_review(reviewer_id="c-1")
        with pytest.raises(ReviewAlreadySubmittedError):
            await SubmitReviewUseCase(FakeTaskRepo([task]), FakeReviewRepo([existing])).execute(
                "t-1", "c-1", SubmitReviewRequest(rating=5.0, comment="again")
            )


# ── List Reviews ───────────────────────────────────────────────────────────────


class TestListReviewsUseCase:
    async def test_list_task_reviews(self):
        reviews = [make_review("r-1"), make_review("r-2")]
        result = await ListTaskReviewsUseCase(FakeReviewRepo(reviews)).execute("t-1")
        assert len(result) == 2

    async def test_list_task_reviews_only_revealed(self):
        reviews = [make_review("r-1", is_revealed=True), make_review("r-2", is_revealed=False)]
        result = await ListTaskReviewsUseCase(FakeReviewRepo(reviews)).execute("t-1", only_revealed=True)
        assert len(result) == 1

    async def test_list_user_reviews(self):
        reviews = [make_review("r-1"), make_review("r-2")]
        result = await ListUserReviewsUseCase(FakeReviewRepo(reviews)).execute("h-1")
        assert len(result) == 2
