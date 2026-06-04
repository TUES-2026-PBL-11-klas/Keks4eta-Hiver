"""Unit tests for message, dispute, and notification use cases."""
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

from src.application.use_cases.disputes.dispute_use_cases import (
    GetDisputeUseCase,
    OpenDisputeUseCase,
    ResolveDisputeUseCase,
)
from src.application.use_cases.messages.message_use_cases import (
    ListMessagesUseCase,
    SendMessageUseCase,
)
from src.application.use_cases.notifications.notification_use_cases import (
    CountUnreadUseCase,
    ListNotificationsUseCase,
    MarkAllNotificationsReadUseCase,
    MarkNotificationReadUseCase,
)
from src.domain.entities.dispute import Dispute
from src.domain.entities.message import Message
from src.domain.entities.notification import Notification
from src.domain.entities.task import Task
from src.domain.entities.transaction import Transaction
from src.domain.errors.domain_errors import (
    DisputeAlreadyExistsError,
    DisputeNotFoundError,
    NoEscrowToDisputeError,
    TaskNotFoundError,
    UnauthorizedActionError,
)
from src.domain.value_objects.money import Money


# ─── Shared fakes ──────────────────────────────────────────────────────────────


def make_accepted_task(tid: str = "t-1", client_id: str = "c-1", hiver_id: str = "h-1") -> Task:
    task = Task(
        id=tid, client_id=client_id, vertical="home", subcategory="cleaning",
        title="Clean house", description="Needs cleaning",
    )
    task.accept(hiver_id)
    return task


def make_transaction(task_id: str = "t-1") -> Transaction:
    return Transaction.create_for_task(
        id="txn-1", task_id=task_id, client_id="c-1", hiver_id="h-1",
        offer_price=Money.of(100), stripe_payment_intent_id="pi_mock",
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


class FakeMessageRepo:
    def __init__(self) -> None:
        self.messages: list[Message] = []
        self.marked_read: list[tuple[str, str]] = []

    async def add(self, message: Message) -> Message:
        self.messages.append(message)
        return message

    async def list_for_task(self, task_id: str) -> list[Message]:
        return [m for m in self.messages if m.task_id == task_id]

    async def mark_read_for_reader(self, task_id: str, reader_id: str) -> int:
        self.marked_read.append((task_id, reader_id))
        return 0


class FakeDisputeRepo:
    def __init__(self, disputes: list | None = None) -> None:
        self.saved: list = disputes or []

    async def add(self, dispute: Dispute) -> Dispute:
        self.saved.append(dispute)
        return dispute

    async def find_by_task(self, task_id: str):
        return next((d for d in self.saved if d.task_id == task_id), None)

    async def save(self, dispute: Dispute) -> Dispute:
        for i, d in enumerate(self.saved):
            if d.id == dispute.id:
                self.saved[i] = dispute
                return dispute
        self.saved.append(dispute)
        return dispute


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
        self.released: list[str] = []
        self.refunded: list[str] = []

    async def hold_payment(self, amount, customer_id: str) -> str:
        return "pi_mock"

    async def release_payment(self, intent_id: str) -> None:
        self.released.append(intent_id)

    async def refund_payment(self, intent_id: str, amount) -> None:
        self.refunded.append(intent_id)

    async def create_customer(self, email: str, name: str) -> str:
        return "cus_mock"


class FakeNotificationRepo:
    def __init__(self, notifications: list | None = None) -> None:
        self.saved: list[Notification] = notifications or []

    async def list_for_user(self, user_id: str, only_unread: bool = False, limit: int = 50):
        items = [n for n in self.saved if n.user_id == user_id]
        if only_unread:
            items = [n for n in items if not n.is_read]
        return items[:limit]

    async def count_unread(self, user_id: str) -> int:
        return sum(1 for n in self.saved if n.user_id == user_id and not n.is_read)

    async def mark_read(self, notification_id: str, user_id: str) -> bool:
        for n in self.saved:
            if n.id == notification_id and n.user_id == user_id:
                n.is_read = True
                return True
        return False

    async def mark_all_read(self, user_id: str) -> int:
        count = 0
        for n in self.saved:
            if n.user_id == user_id and not n.is_read:
                n.is_read = True
                count += 1
        return count


# ─── Message Use Cases ─────────────────────────────────────────────────────────


class TestSendMessageUseCase:
    async def test_client_sends_message(self):
        task = make_accepted_task()
        msg_repo = FakeMessageRepo()
        resp = await SendMessageUseCase(FakeTaskRepo([task]), msg_repo).execute(
            "t-1", "c-1", "Hello hiver!"
        )
        assert resp.sender_id == "c-1"
        assert resp.content == "Hello hiver!"
        assert len(msg_repo.messages) == 1

    async def test_hiver_sends_message(self):
        task = make_accepted_task()
        msg_repo = FakeMessageRepo()
        resp = await SendMessageUseCase(FakeTaskRepo([task]), msg_repo).execute(
            "t-1", "h-1", "On my way!"
        )
        assert resp.sender_id == "h-1"

    async def test_task_not_found_raises(self):
        with pytest.raises(TaskNotFoundError):
            await SendMessageUseCase(FakeTaskRepo(), FakeMessageRepo()).execute(
                "nope", "c-1", "hello"
            )

    async def test_stranger_cannot_message(self):
        task = make_accepted_task()
        with pytest.raises(UnauthorizedActionError):
            await SendMessageUseCase(FakeTaskRepo([task]), FakeMessageRepo()).execute(
                "t-1", "stranger", "hi"
            )

    async def test_long_message_preview_truncated(self):
        task = make_accepted_task()
        msg_repo = FakeMessageRepo()
        long_content = "A" * 200
        resp = await SendMessageUseCase(FakeTaskRepo([task]), msg_repo).execute(
            "t-1", "c-1", long_content
        )
        assert resp.content == long_content


class TestListMessagesUseCase:
    async def test_lists_and_marks_read(self):
        task = make_accepted_task()
        msg_repo = FakeMessageRepo()
        msg_repo.messages = [
            Message(id="m-1", task_id="t-1", sender_id="h-1", content="Hello")
        ]

        result = await ListMessagesUseCase(FakeTaskRepo([task]), msg_repo).execute("t-1", "c-1")
        assert len(result) == 1
        assert ("t-1", "c-1") in msg_repo.marked_read

    async def test_task_not_found_raises(self):
        with pytest.raises(TaskNotFoundError):
            await ListMessagesUseCase(FakeTaskRepo(), FakeMessageRepo()).execute("nope", "c-1")

    async def test_stranger_cannot_list(self):
        task = make_accepted_task()
        with pytest.raises(UnauthorizedActionError):
            await ListMessagesUseCase(FakeTaskRepo([task]), FakeMessageRepo()).execute(
                "t-1", "stranger"
            )


# ─── Dispute Use Cases ─────────────────────────────────────────────────────────


class TestOpenDisputeUseCase:
    async def test_client_opens_dispute(self):
        task = make_accepted_task()
        task.start("h-1")
        txn = make_transaction()
        dispute_repo = FakeDisputeRepo()

        resp = await OpenDisputeUseCase(
            FakeTaskRepo([task]), dispute_repo, FakeTransactionRepo([txn])
        ).execute("t-1", "c-1", "Work not done")

        assert resp.reason == "Work not done"
        assert len(dispute_repo.saved) == 1

    async def test_task_not_found_raises(self):
        with pytest.raises(TaskNotFoundError):
            await OpenDisputeUseCase(
                FakeTaskRepo(), FakeDisputeRepo(), FakeTransactionRepo()
            ).execute("nope", "c-1", "reason")

    async def test_no_escrow_raises(self):
        task = make_accepted_task()
        with pytest.raises(NoEscrowToDisputeError):
            await OpenDisputeUseCase(
                FakeTaskRepo([task]), FakeDisputeRepo(), FakeTransactionRepo()
            ).execute("t-1", "c-1", "reason")

    async def test_duplicate_dispute_raises(self):
        task = make_accepted_task()
        txn = make_transaction()
        existing = Dispute(id="d-1", task_id="t-1", opened_by_id="c-1", reason="Already open")
        with pytest.raises(DisputeAlreadyExistsError):
            await OpenDisputeUseCase(
                FakeTaskRepo([task]), FakeDisputeRepo([existing]), FakeTransactionRepo([txn])
            ).execute("t-1", "c-1", "again")


class TestResolveDisputeUseCase:
    async def _setup(self):
        task = make_accepted_task()
        task.start("h-1")
        txn = make_transaction()
        txn.dispute()
        dispute = Dispute(id="d-1", task_id="t-1", opened_by_id="c-1", reason="Problem")
        return task, txn, dispute

    async def test_client_concedes_releases_to_hiver(self):
        task, txn, dispute = await self._setup()
        payment = FakePaymentPort()
        resp = await ResolveDisputeUseCase(
            FakeTaskRepo([task]), FakeDisputeRepo([dispute]),
            FakeTransactionRepo([txn]), payment
        ).execute("t-1", "c-1")
        assert resp.status == "resolved"
        assert "pi_mock" in payment.released

    async def test_hiver_concedes_refunds_to_client(self):
        task, txn, dispute = await self._setup()
        payment = FakePaymentPort()
        resp = await ResolveDisputeUseCase(
            FakeTaskRepo([task]), FakeDisputeRepo([dispute]),
            FakeTransactionRepo([txn]), payment
        ).execute("t-1", "h-1")
        assert resp.status == "refunded"
        assert "pi_mock" in payment.refunded

    async def test_task_not_found_raises(self):
        with pytest.raises(TaskNotFoundError):
            await ResolveDisputeUseCase(
                FakeTaskRepo(), FakeDisputeRepo(), FakeTransactionRepo(), FakePaymentPort()
            ).execute("nope", "c-1")

    async def test_dispute_not_found_raises(self):
        task = make_accepted_task()
        with pytest.raises(DisputeNotFoundError):
            await ResolveDisputeUseCase(
                FakeTaskRepo([task]), FakeDisputeRepo(), FakeTransactionRepo(), FakePaymentPort()
            ).execute("t-1", "c-1")


class TestGetDisputeUseCase:
    async def test_returns_dispute(self):
        task = make_accepted_task()
        dispute = Dispute(id="d-1", task_id="t-1", opened_by_id="c-1", reason="Issue")
        resp = await GetDisputeUseCase(FakeTaskRepo([task]), FakeDisputeRepo([dispute])).execute(
            "t-1", "c-1"
        )
        assert resp is not None
        assert resp.id == "d-1"

    async def test_returns_none_when_no_dispute(self):
        task = make_accepted_task()
        resp = await GetDisputeUseCase(FakeTaskRepo([task]), FakeDisputeRepo()).execute(
            "t-1", "c-1"
        )
        assert resp is None

    async def test_task_not_found_raises(self):
        with pytest.raises(TaskNotFoundError):
            await GetDisputeUseCase(FakeTaskRepo(), FakeDisputeRepo()).execute("nope", "c-1")


# ─── Notification Use Cases ────────────────────────────────────────────────────


def make_notification(nid: str = "n-1", user_id: str = "u-1", is_read: bool = False):
    return Notification(
        id=nid, user_id=user_id, title="Test", body="Body", is_read=is_read,
        sent_at=datetime.utcnow(),
    )


class TestListNotificationsUseCase:
    async def test_lists_all(self):
        notifs = [make_notification("n-1"), make_notification("n-2")]
        result = await ListNotificationsUseCase(FakeNotificationRepo(notifs)).execute("u-1")
        assert len(result) == 2

    async def test_lists_only_unread(self):
        notifs = [make_notification("n-1", is_read=True), make_notification("n-2")]
        result = await ListNotificationsUseCase(FakeNotificationRepo(notifs)).execute(
            "u-1", only_unread=True
        )
        assert len(result) == 1

    async def test_empty_when_no_notifications(self):
        result = await ListNotificationsUseCase(FakeNotificationRepo()).execute("u-1")
        assert result == []


class TestCountUnreadUseCase:
    async def test_counts_unread(self):
        notifs = [
            make_notification("n-1", is_read=False),
            make_notification("n-2", is_read=True),
            make_notification("n-3", is_read=False),
        ]
        count = await CountUnreadUseCase(FakeNotificationRepo(notifs)).execute("u-1")
        assert count == 2

    async def test_zero_when_all_read(self):
        notifs = [make_notification("n-1", is_read=True)]
        count = await CountUnreadUseCase(FakeNotificationRepo(notifs)).execute("u-1")
        assert count == 0


class TestMarkNotificationReadUseCase:
    async def test_marks_single_notification_read(self):
        notif = make_notification("n-1")
        repo = FakeNotificationRepo([notif])
        result = await MarkNotificationReadUseCase(repo).execute("n-1", "u-1")
        assert result is True
        assert notif.is_read is True

    async def test_returns_false_for_missing(self):
        result = await MarkNotificationReadUseCase(FakeNotificationRepo()).execute("missing", "u-1")
        assert result is False


class TestMarkAllNotificationsReadUseCase:
    async def test_marks_all_unread(self):
        notifs = [make_notification("n-1"), make_notification("n-2")]
        count = await MarkAllNotificationsReadUseCase(FakeNotificationRepo(notifs)).execute("u-1")
        assert count == 2
        assert all(n.is_read for n in notifs)

    async def test_zero_when_already_read(self):
        notifs = [make_notification("n-1", is_read=True)]
        count = await MarkAllNotificationsReadUseCase(FakeNotificationRepo(notifs)).execute("u-1")
        assert count == 0
