from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar

from domain.entities.boost import Boost
from domain.entities.dispute import Dispute
from domain.entities.message import Message
from domain.entities.notification import Notification
from domain.entities.offer import Offer
from domain.entities.review import Review
from domain.entities.task import Task
from domain.entities.transaction import Transaction
from domain.entities.user import Client, Hiver
from domain.value_objects.location import Location

T = TypeVar("T")
ID = TypeVar("ID", str, int)


# ── Generic Base ────────────────────────────────────────────────────────────


class IRepository[T, ID: (str, int)](ABC):
    """
    Generic repository interface.
    OOP: Generics — one interface works for User, Task, Offer, etc.
    Avoids duplicating find_by_id / save / delete for every entity.
    """

    @abstractmethod
    async def find_by_id(self, entity_id: ID) -> T | None: ...

    @abstractmethod
    async def save(self, entity: T) -> T: ...

    @abstractmethod
    async def delete(self, entity_id: ID) -> None: ...


@dataclass
class PaginatedResult[T]:
    """Generic paginated response — works for any entity type."""

    items: list[T]
    total: int
    page: int
    page_size: int

    @property
    def has_next(self) -> bool:
        return (self.page * self.page_size) < self.total

    @property
    def total_pages(self) -> int:
        return -(-self.total // self.page_size)  # ceiling division


# ── Result / Railway-oriented error handling ────────────────────────────────

E = TypeVar("E", bound="Exception")


@dataclass(frozen=True)
class Success[T]:
    data: T
    success: bool = True


@dataclass(frozen=True)
class Failure[E: "Exception"]:
    error: E
    success: bool = False


Result = Success[T] | Failure[Exception]  # type alias


# ── Interface Segregation (SOLID — I) ───────────────────────────────────────


class IReadableTaskRepository(ABC):
    """Read-only subset — used by public search, does not depend on writes."""

    @abstractmethod
    async def find_by_id(self, task_id: str) -> Task | None: ...

    @abstractmethod
    async def find_nearby(
        self, location: Location, radius_km: int, vertical: str | None = None
    ) -> list[Task]: ...

    @abstractmethod
    async def find_by_client(
        self, client_id: str, page: int = 1, page_size: int = 20
    ) -> PaginatedResult[Task]: ...

    @abstractmethod
    async def search(
        self,
        vertical: str | None = None,
        status: str | None = None,
        is_urgent: bool | None = None,
        min_budget: float | None = None,
        max_budget: float | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResult[Task]: ...


class IWritableTaskRepository(ABC):
    """Write subset — used by task management services."""

    @abstractmethod
    async def save(self, task: Task) -> Task: ...

    @abstractmethod
    async def update_status(self, task_id: str, status: str) -> None: ...

    @abstractmethod
    async def delete(self, task_id: str) -> None: ...


class ITaskRepository(IReadableTaskRepository, IWritableTaskRepository):
    """Full repository — used by admin and task management services."""


# ── Concrete Repository Interfaces ──────────────────────────────────────────


class IClientRepository(IRepository[Client, str], ABC):
    @abstractmethod
    async def find_by_email(self, email: str) -> Client | None: ...

    @abstractmethod
    async def find_by_oauth(self, provider: str, oauth_id: str) -> Client | None: ...

    @abstractmethod
    async def find_all(
        self, page: int = 1, page_size: int = 20
    ) -> PaginatedResult[Client]: ...


class IHiverRepository(IRepository[Hiver, str], ABC):
    @abstractmethod
    async def find_by_email(self, email: str) -> Hiver | None: ...

    @abstractmethod
    async def find_by_oauth(self, provider: str, oauth_id: str) -> Hiver | None: ...

    @abstractmethod
    async def find_available_near(
        self, location: Location, radius_km: int, vertical: str | None = None
    ) -> list[Hiver]: ...

    @abstractmethod
    async def find_all(
        self, page: int = 1, page_size: int = 20
    ) -> PaginatedResult[Hiver]: ...


class IOfferRepository(IRepository[Offer, str], ABC):
    @abstractmethod
    async def find_by_task(self, task_id: str) -> list[Offer]: ...

    @abstractmethod
    async def find_by_hiver(self, hiver_id: str) -> list[Offer]: ...

    @abstractmethod
    async def find_by_task_and_hiver(
        self, task_id: str, hiver_id: str
    ) -> Offer | None: ...


class ITransactionRepository(IRepository[Transaction, str], ABC):
    @abstractmethod
    async def find_by_task(self, task_id: str) -> Transaction | None: ...

    @abstractmethod
    async def find_by_hiver(self, hiver_id: str) -> list[Transaction]: ...


class IBoostRepository(ABC):
    """Paid hiver visibility boosts."""

    @abstractmethod
    async def add(self, boost: Boost) -> Boost: ...

    @abstractmethod
    async def find_active_for_hiver(self, hiver_id: str) -> Boost | None: ...

    @abstractmethod
    async def active_hiver_ids(self, vertical: str | None = None) -> set[str]:
        """Ids of hivers with a currently-active boost applicable to `vertical`."""
        ...


class IDisputeRepository(ABC):
    """One dispute per task (DB-unique on task_id)."""

    @abstractmethod
    async def add(self, dispute: Dispute) -> Dispute: ...

    @abstractmethod
    async def find_by_task(self, task_id: str) -> Dispute | None: ...

    @abstractmethod
    async def save(self, dispute: Dispute) -> Dispute: ...


class IMessageRepository(ABC):
    """Task chat messages between the client and the assigned hiver."""

    @abstractmethod
    async def add(self, message: Message) -> Message: ...

    @abstractmethod
    async def list_for_task(self, task_id: str) -> list[Message]: ...

    @abstractmethod
    async def mark_read_for_reader(self, task_id: str, reader_id: str) -> int:
        """Mark messages the reader received (sender != reader) as read."""
        ...


class INotificationRepository(ABC):
    """Read side of the in-app notification feed (writes go through INotificationPort)."""

    @abstractmethod
    async def list_for_user(
        self, user_id: str, only_unread: bool = False, limit: int = 50
    ) -> list[Notification]: ...

    @abstractmethod
    async def count_unread(self, user_id: str) -> int: ...

    @abstractmethod
    async def mark_read(self, notification_id: str, user_id: str) -> bool: ...

    @abstractmethod
    async def mark_all_read(self, user_id: str) -> int: ...


class IReviewRepository(IRepository[Review, str], ABC):
    @abstractmethod
    async def find_by_task(self, task_id: str) -> list[Review]: ...

    @abstractmethod
    async def find_by_reviewee(self, reviewee_id: str) -> list[Review]: ...

    @abstractmethod
    async def find_by_task_and_reviewer(
        self, task_id: str, reviewer_id: str
    ) -> Review | None: ...
