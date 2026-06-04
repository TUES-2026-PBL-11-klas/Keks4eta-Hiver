import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[3]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

import pytest

from src.domain.entities.task import Task, TaskStatus
from src.domain.errors.domain_errors import (
    InvalidBudgetRangeError,
    InvalidVerticalError,
    TaskAlreadyAcceptedError,
    TaskNotCompletedError,
    UnauthorizedActionError,
)
from src.domain.value_objects.money import Money


def make_task(**overrides) -> Task:
    defaults = dict(
        id="t1",
        client_id="c1",
        vertical="home",
        subcategory="cleaning",
        title="Clean my flat",
        description="2 rooms",
    )
    defaults.update(overrides)
    return Task(**defaults)


class TestTaskConstruction:
    def test_defaults_to_open(self):
        assert make_task().status == TaskStatus.OPEN
        assert make_task().is_open()

    def test_invalid_vertical_rejected(self):
        with pytest.raises(InvalidVerticalError):
            make_task(vertical="spaceship")


class TestTaskLifecycle:
    def test_accept_moves_open_to_accepted(self):
        task = make_task()
        task.accept("h1")
        assert task.status == TaskStatus.ACCEPTED
        assert task.hiver_id == "h1"

    def test_cannot_accept_twice(self):
        task = make_task()
        task.accept("h1")
        with pytest.raises(TaskAlreadyAcceptedError):
            task.accept("h2")

    def test_start_requires_the_assigned_hiver(self):
        task = make_task()
        task.accept("h1")
        with pytest.raises(UnauthorizedActionError):
            task.start("someone-else")
        task.start("h1")
        assert task.status == TaskStatus.IN_PROGRESS

    def test_complete_happy_path(self):
        task = make_task()
        task.accept("h1")
        task.start("h1")
        task.complete("c1")
        assert task.is_completed()

    def test_complete_requires_client(self):
        task = make_task()
        task.accept("h1")
        task.start("h1")
        with pytest.raises(UnauthorizedActionError):
            task.complete("h1")

    def test_complete_requires_in_progress(self):
        task = make_task()  # still OPEN
        with pytest.raises(TaskNotCompletedError):
            task.complete("c1")

    def test_cancel_by_client(self):
        task = make_task()
        task.cancel("c1")
        assert task.status == TaskStatus.CANCELLED

    def test_cancel_by_stranger_rejected(self):
        task = make_task()
        with pytest.raises(UnauthorizedActionError):
            task.cancel("stranger")

    def test_cannot_cancel_completed(self):
        task = make_task()
        task.accept("h1")
        task.start("h1")
        task.complete("c1")
        with pytest.raises(TaskNotCompletedError):
            task.cancel("c1")


class TestTaskBudget:
    def test_midpoint_with_range(self):
        task = make_task(budget_min=Money.of(20), budget_max=Money.of(40))
        assert task.budget_midpoint() == Money.of(30)

    def test_midpoint_with_only_min(self):
        task = make_task(budget_min=Money.of(20))
        assert task.budget_midpoint() == Money.of(20)

    def test_midpoint_with_no_budget(self):
        assert make_task().budget_midpoint() is None

    def test_max_below_min_rejected(self):
        with pytest.raises(InvalidBudgetRangeError):
            make_task(budget_min=Money.of(100), budget_max=Money.of(50))

    def test_equal_min_and_max_allowed(self):
        task = make_task(budget_min=Money.of(50), budget_max=Money.of(50))
        assert task.budget_midpoint() == Money.of(50)
