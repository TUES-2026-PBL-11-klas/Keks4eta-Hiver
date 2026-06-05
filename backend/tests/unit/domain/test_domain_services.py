"""Unit tests for domain services: EventBus, TaskFactory, notify."""
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

from src.domain.errors.domain_errors import InvalidVerticalError
from src.domain.services.event_bus import DomainEvent, EventBus, notify
from src.domain.services.task_factory import TaskCreateData, TaskFactory


class TestEventBus:
    async def test_subscribe_and_publish(self):
        bus = EventBus()
        received: list[DomainEvent] = []

        async def handler(event: DomainEvent) -> None:
            received.append(event)

        bus.subscribe("test.event", handler)
        await bus.publish(DomainEvent(event_type="test.event", payload={"key": "value"}))

        assert len(received) == 1
        assert received[0].payload["key"] == "value"

    async def test_publish_no_handlers_is_noop(self):
        bus = EventBus()
        await bus.publish(DomainEvent(event_type="unknown", payload={}))

    async def test_multiple_handlers(self):
        bus = EventBus()
        calls: list[str] = []

        async def h1(e: DomainEvent) -> None:
            calls.append("h1")

        async def h2(e: DomainEvent) -> None:
            calls.append("h2")

        bus.subscribe("evt", h1)
        bus.subscribe("evt", h2)
        await bus.publish(DomainEvent("evt", {}))

        assert "h1" in calls
        assert "h2" in calls

    async def test_clear_specific_event(self):
        bus = EventBus()
        calls: list[str] = []

        async def h(e: DomainEvent) -> None:
            calls.append("called")

        bus.subscribe("evt", h)
        bus.clear("evt")
        await bus.publish(DomainEvent("evt", {}))

        assert calls == []

    async def test_clear_all(self):
        bus = EventBus()
        calls: list[str] = []

        async def h(e: DomainEvent) -> None:
            calls.append("called")

        bus.subscribe("a", h)
        bus.subscribe("b", h)
        bus.clear()
        await bus.publish(DomainEvent("a", {}))
        await bus.publish(DomainEvent("b", {}))

        assert calls == []


class TestNotifyHelper:
    async def test_notify_with_bus_publishes_event(self):
        bus = EventBus()
        received: list[DomainEvent] = []

        async def handler(event: DomainEvent) -> None:
            received.append(event)

        bus.subscribe("notify", handler)
        await notify(bus, "user-1", "Title", "Body", {"task_id": "t-1"})

        assert len(received) == 1
        assert received[0].payload["recipient_id"] == "user-1"
        assert received[0].payload["title"] == "Title"

    async def test_notify_without_bus_is_noop(self):
        await notify(None, "user-1", "Title", "Body")

    async def test_notify_without_data_defaults_empty(self):
        bus = EventBus()
        received: list[DomainEvent] = []

        async def handler(event: DomainEvent) -> None:
            received.append(event)

        bus.subscribe("notify", handler)
        await notify(bus, "user-1", "T", "B")
        assert received[0].payload["data"] == {}


class TestTaskFactory:
    def _data(self, vertical: str = "home", **kwargs) -> TaskCreateData:
        return TaskCreateData(
            client_id="c-1",
            vertical=vertical,
            subcategory="general",
            title="Test Task",
            description="A test",
            smart_answers={},
            **kwargs,
        )

    def test_creates_home_task(self):
        task = TaskFactory.create(self._data("home"))
        assert task.vertical == "home"
        assert task.client_id == "c-1"

    def test_creates_learn_task(self):
        task = TaskFactory.create(self._data("learn"))
        assert task.vertical == "learn"

    def test_creates_tech_task(self):
        task = TaskFactory.create(self._data("tech"))
        assert task.vertical == "tech"

    def test_creates_care_task(self):
        task = TaskFactory.create(self._data("care"))
        assert task.vertical == "care"

    def test_creates_move_task(self):
        task = TaskFactory.create(self._data("move"))
        assert task.vertical == "move"

    def test_creates_events_task(self):
        task = TaskFactory.create(self._data("events"))
        assert task.vertical == "events"

    def test_invalid_vertical_raises(self):
        with pytest.raises(InvalidVerticalError):
            TaskFactory.create(self._data("invalid"))

    def test_task_with_budget(self):
        task = TaskFactory.create(self._data("home", budget_min=50.0, budget_max=200.0))
        assert task.budget_min is not None
        assert float(task.budget_min.value) == 50.0

    def test_task_is_urgent(self):
        task = TaskFactory.create(self._data("home", is_urgent=True))
        assert task.is_urgent is True

    def test_task_with_location(self):
        task = TaskFactory.create(self._data("home", latitude=42.0, longitude=23.0, location_display="Sofia"))
        assert task.location is not None
        assert task.location.display_address == "Sofia"

    def test_task_id_is_unique(self):
        t1 = TaskFactory.create(self._data("home"))
        t2 = TaskFactory.create(self._data("home"))
        assert t1.id != t2.id


from src.domain.services.search_sort import (  # noqa: E402
    HiverSearchResult,
    SortByDistance,
    SortByPrice,
    SortByRating,
    SortByRecommended,
    get_sort_strategy,
)


def make_hiver_result(hid: str, rating: float = 4.0, distance: float = 1000.0,
                       price: float = 100.0, is_boosted: bool = False) -> HiverSearchResult:
    return HiverSearchResult(
        hiver_id=hid, avg_rating=rating, distance_m=distance,
        min_price=price, response_rate=0.9, is_boosted=is_boosted,
    )


class TestSearchSortStrategies:
    def test_sort_by_rating_descending(self):
        hivers = [make_hiver_result("h1", rating=3.0), make_hiver_result("h2", rating=5.0)]
        result = SortByRating().sort(hivers)
        assert result[0].hiver_id == "h2"

    def test_sort_by_distance_ascending(self):
        hivers = [make_hiver_result("h1", distance=5000), make_hiver_result("h2", distance=500)]
        result = SortByDistance().sort(hivers)
        assert result[0].hiver_id == "h2"

    def test_sort_by_price_ascending(self):
        hivers = [make_hiver_result("h1", price=200), make_hiver_result("h2", price=50)]
        result = SortByPrice().sort(hivers)
        assert result[0].hiver_id == "h2"

    def test_sort_by_recommended(self):
        hivers = [
            make_hiver_result("h1", rating=5.0, distance=100, is_boosted=True),
            make_hiver_result("h2", rating=3.0, distance=5000),
        ]
        result = SortByRecommended().sort(hivers)
        assert result[0].hiver_id == "h1"

    def test_get_sort_strategy_rating(self):
        strategy = get_sort_strategy("rating")
        assert isinstance(strategy, SortByRating)

    def test_get_sort_strategy_distance(self):
        strategy = get_sort_strategy("distance")
        assert isinstance(strategy, SortByDistance)

    def test_get_sort_strategy_price(self):
        strategy = get_sort_strategy("price")
        assert isinstance(strategy, SortByPrice)

    def test_get_sort_strategy_recommended(self):
        strategy = get_sort_strategy("recommended")
        assert isinstance(strategy, SortByRecommended)

    def test_get_sort_strategy_invalid_raises(self):
        with pytest.raises(ValueError):
            get_sort_strategy("invalid")
