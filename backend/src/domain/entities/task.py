from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from domain.value_objects.money import Money
from domain.value_objects.location import Location
from domain.errors.domain_errors import (
    TaskAlreadyAcceptedError,
    TaskNotCompletedError,
    UnauthorizedActionError,
)


class TaskStatus(str, Enum):
    OPEN = "open"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"


VALID_VERTICALS = {"home", "learn", "tech", "care", "move", "events"}


@dataclass
class Task:
    """
    Domain entity: a task posted by a Client.

    OOP: Encapsulation — status transitions are enforced via methods,
    never by direct assignment from outside the class.
    """
    id: str
    client_id: str
    vertical: str
    subcategory: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.OPEN
    hiver_id: str | None = None
    budget_min: Money | None = None
    budget_max: Money | None = None
    is_urgent: bool = False
    location: Location | None = None
    smart_answers: dict = field(default_factory=dict)
    image_urls: list[str] = field(default_factory=list)
    expires_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        from domain.errors.domain_errors import InvalidVerticalError
        if self.vertical not in VALID_VERTICALS:
            raise InvalidVerticalError(self.vertical)

    # ── State transitions (Encapsulation: only valid transitions allowed) ──

    def accept(self, hiver_id: str) -> None:
        """Hiver accepts the task — moves from OPEN → ACCEPTED."""
        if self.status != TaskStatus.OPEN:
            raise TaskAlreadyAcceptedError(self.id)
        self.hiver_id = hiver_id
        self.status = TaskStatus.ACCEPTED
        self._touch()

    def start(self, actor_id: str) -> None:
        """Hiver starts work — moves ACCEPTED → IN_PROGRESS."""
        self._assert_hiver(actor_id)
        self.status = TaskStatus.IN_PROGRESS
        self._touch()

    def complete(self, actor_id: str) -> None:
        """Client marks task done — moves IN_PROGRESS → COMPLETED."""
        if actor_id != self.client_id:
            raise UnauthorizedActionError("complete this task")
        if self.status != TaskStatus.IN_PROGRESS:
            raise TaskNotCompletedError(self.id)
        self.status = TaskStatus.COMPLETED
        self._touch()

    def cancel(self, actor_id: str) -> None:
        """Client or hiver cancels — only allowed before IN_PROGRESS."""
        if actor_id not in (self.client_id, self.hiver_id):
            raise UnauthorizedActionError("cancel this task")
        if self.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
            raise TaskNotCompletedError(self.id)
        self.status = TaskStatus.CANCELLED
        self._touch()

    def open_dispute(self) -> None:
        """Either party flags a problem — locks the task while escrow is reviewed."""
        self.status = TaskStatus.DISPUTED
        self._touch()

    def resolve_dispute(self, *, release: bool) -> None:
        """Resolve a dispute: release → COMPLETED (hiver paid), refund → CANCELLED."""
        if self.status != TaskStatus.DISPUTED:
            raise TaskNotCompletedError(self.id)
        self.status = TaskStatus.COMPLETED if release else TaskStatus.CANCELLED
        self._touch()

    def is_open(self) -> bool:
        return self.status == TaskStatus.OPEN

    def is_completed(self) -> bool:
        return self.status == TaskStatus.COMPLETED

    def budget_midpoint(self) -> Money | None:
        if self.budget_min and self.budget_max:
            return (self.budget_min + self.budget_max) * 0.5
        return self.budget_min or self.budget_max

    def _assert_hiver(self, actor_id: str) -> None:
        if actor_id != self.hiver_id:
            raise UnauthorizedActionError("perform this action on the task")

    def _touch(self) -> None:
        self.updated_at = datetime.utcnow()
