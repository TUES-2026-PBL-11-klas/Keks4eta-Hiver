"""Unit tests for boost, find-hivers-nearby, and upload-task-image use cases."""
import os
import sys
from datetime import UTC, datetime, timedelta
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

from src.application.use_cases.boosts.boost_use_cases import (
    BuyBoostUseCase,
    GetMyBoostUseCase,
)
from src.application.use_cases.tasks.upload_task_image_use_case import (
    UploadTaskImageUseCase,
)
from src.application.use_cases.users.find_hivers_nearby_use_case import (
    FindHiversNearbyUseCase,
)
from src.domain.entities.boost import Boost
from src.domain.entities.task import Task
from src.domain.entities.user import Hiver
from src.domain.errors.domain_errors import (
    BusinessRuleViolationError,
    TaskNotFoundError,
    UnauthorizedActionError,
)
from src.domain.value_objects.location import Location
from src.domain.value_objects.money import Money
from src.domain.value_objects.rating import Rating
from src.domain.value_objects.work_radius import WorkRadius


def _valid_image_bytes() -> bytes:
    """A real, decodable PNG — the upload use case now validates image integrity."""
    from io import BytesIO

    from PIL import Image

    buf = BytesIO()
    Image.new("RGB", (4, 4), (238, 127, 34)).save(buf, format="PNG")
    return buf.getvalue()


# ── Fakes ─────────────────────────────────────────────────────────────────────


class FakeBoostRepo:
    def __init__(self, boosts: list | None = None) -> None:
        self.saved: list[Boost] = boosts or []

    async def add(self, boost: Boost) -> Boost:
        self.saved.append(boost)
        return boost

    async def find_active_for_hiver(self, hiver_id: str) -> Boost | None:
        return next(
            (b for b in self.saved if b.hiver_id == hiver_id and b.is_active()), None
        )

    async def active_hiver_ids(self, vertical: str | None = None) -> set[str]:
        return {b.hiver_id for b in self.saved if b.is_active()}


class FakePaymentPort:
    def __init__(self) -> None:
        self.held: list[str] = []

    async def hold_payment(self, amount: Money, customer_id: str) -> str:
        self.held.append(customer_id)
        return "pi_mock"

    async def release_payment(self, pi: str) -> None: ...
    async def refund_payment(self, pi: str, amount: Money) -> None: ...
    async def create_customer(self, email: str, name: str) -> str: return "cus_mock"


class FakeHiverRepo:
    def __init__(self, hivers: list | None = None) -> None:
        self.hivers: list[Hiver] = hivers or []

    async def find_available_near(
        self, location: Location, radius_km: int, vertical: str | None = None
    ) -> list[Hiver]:
        return self.hivers

    async def find_by_id(self, hiver_id: str) -> Hiver | None:
        return next((h for h in self.hivers if h.id == hiver_id), None)

    async def find_by_email(self, email: str) -> Hiver | None: return None
    async def find_by_oauth(self, p: str, oid: str) -> Hiver | None: return None
    async def find_all(self, page: int = 1, page_size: int = 20): ...

    async def save(self, hiver: Hiver) -> Hiver:
        self.hivers.append(hiver)
        return hiver

    async def delete(self, hiver_id: str) -> None: ...


def make_hiver(hid: str = "h-1") -> Hiver:
    return Hiver(
        id=hid,
        email=f"{hid}@test.com",
        _password_hash=None,
        full_name="Test Hiver",
        location=Location(latitude=42.0, longitude=23.0),
        avg_rating=Rating(4.5),
        work_radius=WorkRadius(10),
    )


class FakeTaskRepo:
    def __init__(self, tasks: list | None = None) -> None:
        self.saved: list[Task] = tasks or []

    async def find_by_id(self, tid: str) -> Task | None:
        return next((t for t in self.saved if t.id == tid), None)

    async def save(self, task: Task) -> Task:
        for i, t in enumerate(self.saved):
            if t.id == task.id:
                self.saved[i] = task
                return task
        self.saved.append(task)
        return task

    async def search(self, **kwargs): ...
    async def find_nearby(self, *args, **kwargs): return []
    async def find_by_client(self, *args, **kwargs): ...
    async def update_status(self, *args, **kwargs): ...
    async def delete(self, *args, **kwargs): ...


class FakeStoragePort:
    async def upload(self, bucket: str, key: str, data: bytes, content_type: str) -> str:
        return f"https://storage.example.com/{bucket}/{key}"

    async def delete(self, bucket: str, key: str) -> None: ...

    async def get_signed_url(self, bucket: str, key: str, expires_in: int = 3600) -> str:
        return f"https://storage.example.com/{bucket}/{key}?signed=1"


def make_task(tid: str = "t-1", client_id: str = "c-1") -> Task:
    return Task(
        id=tid, client_id=client_id, vertical="home", subcategory="cleaning",
        title="Test task", description="Needs work",
    )


# ── BuyBoostUseCase ────────────────────────────────────────────────────────────


class TestBuyBoostUseCase:
    async def test_buys_boost_and_returns_response(self):
        boost_repo = FakeBoostRepo()
        payment = FakePaymentPort()
        result = await BuyBoostUseCase(boost_repo, payment).execute("h-1")

        assert result.hiver_id == "h-1"
        assert result.is_active is True
        assert len(boost_repo.saved) == 1
        assert "h-1" in payment.held

    async def test_buys_vertical_scoped_boost(self):
        boost_repo = FakeBoostRepo()
        result = await BuyBoostUseCase(boost_repo, FakePaymentPort()).execute(
            "h-2", vertical="home"
        )
        assert result.vertical == "home"

    async def test_buy_boost_price_is_correct(self):
        from src.application.dtos.boost_dtos import BOOST_PRICE_BGN
        boost_repo = FakeBoostRepo()
        result = await BuyBoostUseCase(boost_repo, FakePaymentPort()).execute("h-1")
        assert result.price_bgn == BOOST_PRICE_BGN


# ── GetMyBoostUseCase ──────────────────────────────────────────────────────────


class TestGetMyBoostUseCase:
    async def test_returns_active_boost(self):
        active_boost = Boost.purchase(
            id="b-1", hiver_id="h-1", stripe_payment_id="pi_mock", days=7
        )
        result = await GetMyBoostUseCase(FakeBoostRepo([active_boost])).execute("h-1")
        assert result is not None
        assert result.id == "b-1"

    async def test_returns_none_when_no_boost(self):
        result = await GetMyBoostUseCase(FakeBoostRepo()).execute("h-1")
        assert result is None

    async def test_returns_none_when_boost_expired(self):
        expired = Boost(
            id="b-2", hiver_id="h-1", stripe_payment_id="pi_x",
            expires_at=datetime.now(UTC) - timedelta(days=1),
        )
        result = await GetMyBoostUseCase(FakeBoostRepo([expired])).execute("h-1")
        assert result is None


# ── FindHiversNearbyUseCase ────────────────────────────────────────────────────


class TestFindHiversNearbyUseCase:
    async def test_returns_empty_when_no_hivers(self):
        results = await FindHiversNearbyUseCase(FakeHiverRepo()).execute(42.0, 23.0)
        assert results == []

    async def test_returns_hiver_result(self):
        hiver = make_hiver()
        results = await FindHiversNearbyUseCase(FakeHiverRepo([hiver])).execute(42.0, 23.0)
        assert len(results) == 1
        assert results[0].user_id == "h-1"
        assert results[0].avg_rating == 4.5

    async def test_boosted_hivers_sorted_first(self):
        h1 = make_hiver("h-1")
        h2 = make_hiver("h-2")
        active_boost = Boost.purchase(
            id="b-1", hiver_id="h-2", stripe_payment_id="pi_mock", days=7
        )
        boost_repo = FakeBoostRepo([active_boost])

        results = await FindHiversNearbyUseCase(
            FakeHiverRepo([h1, h2]), boost_repo=boost_repo
        ).execute(42.0, 23.0)

        assert results[0].user_id == "h-2"
        assert results[0].is_boosted is True

    async def test_hiver_without_location_has_no_distance(self):
        hiver = Hiver(
            id="h-1", email="h@test.com", _password_hash=None, full_name="No-Loc",
            location=None,
        )
        results = await FindHiversNearbyUseCase(FakeHiverRepo([hiver])).execute(42.0, 23.0)
        assert results[0].distance_km is None

    async def test_uses_vertical_filter(self):
        boost_repo = FakeBoostRepo()
        results = await FindHiversNearbyUseCase(
            FakeHiverRepo(), boost_repo=boost_repo
        ).execute(42.0, 23.0, radius_km=5.0, vertical="home")
        assert results == []


# ── UploadTaskImageUseCase ─────────────────────────────────────────────────────


class TestUploadTaskImageUseCase:
    def _make_use_case(self, task: Task | None = None) -> UploadTaskImageUseCase:
        tasks = [task] if task else []
        return UploadTaskImageUseCase(
            task_repo=FakeTaskRepo(tasks), storage_port=FakeStoragePort()
        )

    async def test_task_not_found_raises(self):
        with pytest.raises(TaskNotFoundError):
            await self._make_use_case().execute("t-1", "c-1", b"data", "image/jpeg")

    async def test_unauthorized_raises(self):
        task = make_task()
        with pytest.raises(UnauthorizedActionError):
            await self._make_use_case(task).execute("t-1", "wrong-client", b"data", "image/jpeg")

    async def test_invalid_content_type_raises(self):
        task = make_task()
        with pytest.raises(BusinessRuleViolationError):
            await self._make_use_case(task).execute("t-1", "c-1", b"data", "text/plain")

    async def test_empty_data_raises(self):
        task = make_task()
        with pytest.raises(BusinessRuleViolationError):
            await self._make_use_case(task).execute("t-1", "c-1", b"", "image/jpeg")

    async def test_oversized_image_raises(self):
        task = make_task()
        big_data = b"x" * (5 * 1024 * 1024 + 1)
        with pytest.raises(BusinessRuleViolationError):
            await self._make_use_case(task).execute("t-1", "c-1", big_data, "image/png")

    async def test_too_many_images_raises(self):
        task = make_task()
        task.image_urls = [f"url_{i}" for i in range(6)]
        with pytest.raises(BusinessRuleViolationError):
            await self._make_use_case(task).execute("t-1", "c-1", b"data", "image/jpeg")

    async def test_uploads_image_and_returns_task(self):
        task = make_task()
        result = await self._make_use_case(task).execute(
            "t-1", "c-1", _valid_image_bytes(), "image/png"
        )
        assert result.id == "t-1"
        assert len(task.image_urls) == 1
        assert "storage.example.com" in task.image_urls[0]

    async def test_webp_content_type_accepted(self):
        task = make_task()
        result = await self._make_use_case(task).execute(
            "t-1", "c-1", _valid_image_bytes(), "image/webp"
        )
        assert result.id == "t-1"
