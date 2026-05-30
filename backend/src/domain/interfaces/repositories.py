from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar, Generic

from domain.entities.user import Client, Hiver
from domain.entities.task import Task
from domain.entities.offer import Offer
from domain.entities.transaction import Transaction
from domain.entities.review import Review
from domain.value_objects.location import Location

T = TypeVar("T")
ID = TypeVar("ID", str, int)


# ── Generic Base ────────────────────────────────────────────────────────────

class IRepository(ABC, Generic[T, ID]):
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
class PaginatedResult(Generic[T]):
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
class Success(Generic[T]):
    data: T
    success: bool = True


@dataclass(frozen=True)
class Failure(Generic[E]):  # type: ignore[type-var]
    error: E
    success: bool = False


Result = Success[T] | Failure  # type alias


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
    async def find_all(self, page: int = 1, page_size: int = 20) -> PaginatedResult[Client]: ...


class IHiverRepository(IRepository[Hiver, str], ABC):
    @abstractmethod
    async def find_by_email(self, email: str) -> Hiver | None: ...

    @abstractmethod
    async def find_available_near(
        self, location: Location, radius_km: int, vertical: str | None = None
    ) -> list[Hiver]: ...

    @abstractmethod
    async def find_all(self, page: int = 1, page_size: int = 20) -> PaginatedResult[Hiver]: ...


class IOfferRepository(IRepository[Offer, str], ABC):
    @abstractmethod
    async def find_by_task(self, task_id: str) -> list[Offer]: ...

    @abstractmethod
    async def find_by_hiver(self, hiver_id: str) -> list[Offer]: ...

    @abstractmethod
    async def find_by_task_and_hiver(self, task_id: str, hiver_id: str) -> Offer | None: ...


class ITransactionRepository(IRepository[Transaction, str], ABC):
    @abstractmethod
    async def find_by_task(self, task_id: str) -> Transaction | None: ...

    @abstractmethod
    async def find_by_hiver(self, hiver_id: str) -> list[Transaction]: ...


class IReviewRepository(IRepository[Review, str], ABC):
    @abstractmethod
    async def find_by_task(self, task_id: str) -> list[Review]: ...

    @abstractmethod
    async def find_by_reviewee(self, reviewee_id: str) -> list[Review]: ...

    @abstractmethod
    async def find_by_task_and_reviewer(
        self, task_id: str, reviewer_id: str
    ) -> Review | None: ...
