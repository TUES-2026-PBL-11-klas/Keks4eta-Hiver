# Hiver — Claude Code Prompt (Python/FastAPI)
# Targeting: Отличен (6) по РС, ООП, БД, ВОТ

---

You are helping build **Hiver** — a two-sided micro-services marketplace
connecting clients with everyday needs to skilled executors ("hivers").
This is a school project graded across four subjects:
Software Development (РС), OOP (ООП), Databases (БД),
and Virtualization & Cloud (ВОТ).

**IMPORTANT — Work in phases, not all at once.**
After each phase, stop and wait for confirmation before proceeding.
This allows review, understanding, and clean git commits per phase.

---

## TECH STACK

| Layer              | Technology                          | Why (arguable at defense)                          |
|--------------------|-------------------------------------|----------------------------------------------------|
| Backend framework  | FastAPI                             | Auto-generates OpenAPI/Swagger, native async,      |
|                    |                                     | type hints = less boilerplate than Flask           |
| Validation         | Pydantic v2                         | Runtime type safety, serialization, OpenAPI schema |
| ORM                | SQLAlchemy 2.0 (async)              | Industry standard, clean Repository pattern,       |
|                    |                                     | avoids raw SQL coupling in business logic          |
| Migrations         | Alembic                             | Version-controlled schema changes, up/down support |
| Database           | PostgreSQL 16 + PostGIS             | Relational integrity + geospatial queries          |
| Cache / sessions   | Redis 7                             | Fast key-value, pub/sub for real-time events       |
| Auth               | python-jose (JWT) + passlib (bcrypt)| Stateless, scalable, standard                      |
| Real-time          | Supabase Realtime or Socket.io      | WebSocket abstraction                              |
| Payments           | Stripe (Test Mode)                  | Simulated escrow — full flow, no real money        |
| Storage            | Supabase Storage or Cloudflare R2   | Managed S3-compatible object storage              |
| Maps               | PostGIS + Google Maps API           | Server-side radius queries, client-side rendering  |
| Testing            | pytest + pytest-asyncio + httpx     | Async test support, clean fixtures                 |
| Linting            | ruff + mypy                         | Fast linter, strict type checking                  |
| Package manager    | uv (or poetry)                      | Modern, fast, lockfile support                     |

---

## PHASE 1 — Project Scaffold (First Commit)

Generate only the skeleton. No business logic yet.

### Folder Structure — Clean Architecture:
```
hiver/
├── backend/
│   ├── src/
│   │   ├── domain/
│   │   │   ├── __init__.py
│   │   │   ├── entities/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── user.py
│   │   │   │   ├── task.py
│   │   │   │   ├── offer.py
│   │   │   │   ├── transaction.py
│   │   │   │   └── review.py
│   │   │   ├── value_objects/
│   │   │   │   ├── money.py
│   │   │   │   ├── location.py
│   │   │   │   ├── rating.py
│   │   │   │   └── work_radius.py
│   │   │   ├── errors/
│   │   │   │   └── domain_errors.py
│   │   │   └── interfaces/
│   │   │       ├── repositories.py
│   │   │       └── ports.py
│   │   ├── application/
│   │   │   ├── use_cases/
│   │   │   │   ├── tasks/
│   │   │   │   ├── offers/
│   │   │   │   ├── auth/
│   │   │   │   └── payments/
│   │   │   └── dtos/
│   │   ├── infrastructure/
│   │   │   ├── database/
│   │   │   │   ├── models/
│   │   │   │   ├── repositories/
│   │   │   │   └── migrations/
│   │   │   ├── http/
│   │   │   │   ├── routers/
│   │   │   │   ├── middleware/
│   │   │   │   └── dependencies.py
│   │   │   ├── payments/
│   │   │   ├── notifications/
│   │   │   └── storage/
│   │   ├── shared/
│   │   │   ├── logger.py
│   │   │   ├── config.py
│   │   │   └── container.py
│   │   └── main.py
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── conftest.py
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── alembic.ini
├── frontend/              (React, separate team member)
├── infra/
│   ├── terraform/
│   ├── k8s/
│   ├── prometheus/
│   └── grafana/
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
└── README.md
```

### pyproject.toml dependencies:
```toml
[project]
name = "hiver-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.111.0",
    "uvicorn[standard]>=0.30.0",
    "pydantic>=2.7.0",
    "pydantic-settings>=2.3.0",
    "sqlalchemy[asyncio]>=2.0.30",
    "asyncpg>=0.29.0",
    "alembic>=1.13.0",
    "redis>=5.0.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "stripe>=9.0.0",
    "httpx>=0.27.0",
    "geoalchemy2>=0.15.0",
    "dependency-injector>=4.41.0",
    "structlog>=24.0.0",
    "prometheus-fastapi-instrumentator>=7.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=5.0.0",
    "ruff>=0.4.0",
    "mypy>=1.10.0",
]
```

### .env.example (document every variable — no defaults for secrets):
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/hiver
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://:password@localhost:6379/0

# Auth
JWT_SECRET_KEY=          # min 32 chars, generate with: openssl rand -hex 32
JWT_ALGORITHM=HS256
JWT_ACCESS_EXPIRE_MINUTES=30
JWT_REFRESH_EXPIRE_DAYS=7

# Stripe (Test Mode only for development)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Google Maps
GOOGLE_MAPS_API_KEY=

# Supabase Storage
SUPABASE_URL=
SUPABASE_SERVICE_KEY=

# Firebase (push notifications)
FIREBASE_CREDENTIALS_JSON=

# App
APP_ENV=development        # development | production
APP_HOST=0.0.0.0
APP_PORT=8000
LOG_LEVEL=DEBUG            # DEBUG | INFO | WARNING | ERROR
CORS_ORIGINS=http://localhost:5173
```

---

## PHASE 2 — Domain Layer (Second Commit)

### OOP Requirements — Targeting Отличен (6):

#### Abstract Base Classes with ABC:
```python
# domain/entities/user.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Generic, TypeVar
from domain.value_objects.money import Money
from domain.value_objects.rating import Rating

@dataclass
class User(ABC):
    """
    Abstract base class for all user types.
    Never instantiated directly — always Client or Hiver.
    
    OOP: Abstraction + Encapsulation
    Encapsulates common user behavior; subclasses expose only
    what's relevant to their role.
    """
    id: str
    email: str
    _password_hash: str          # encapsulated — never public
    full_name: str
    phone: str | None = None
    avatar_url: str | None = None

    @abstractmethod
    def get_role(self) -> str:
        """Polymorphism: each subclass returns its own role string."""
        ...

    @abstractmethod
    def calculate_commission(self, amount: Money) -> Money:
        """
        Polymorphism: commission calculation differs by role and level.
        Client pays service fee; Hiver pays platform commission.
        Liskov: any User subtype works wherever User is expected.
        """
        ...

    def verify_password(self, plain: str) -> bool:
        """Encapsulated: password logic stays inside User."""
        from passlib.context import CryptContext
        return CryptContext(schemes=["bcrypt"]).verify(plain, self._password_hash)

    def _validate_email(self, email: str) -> None:
        """Protected helper — shared by all subclasses."""
        if "@" not in email or "." not in email.split("@")[-1]:
            raise InvalidEmailError(email)


@dataclass
class Client(User):
    """
    OOP: Inheritance from User.
    Client-specific behavior: posting tasks, rating hivers, favourites.
    """
    rating_as_client: Rating = field(default_factory=lambda: Rating(5.0))
    total_tasks: int = 0

    def get_role(self) -> str:
        return "client"

    def calculate_commission(self, amount: Money) -> Money:
        # Clients pay 5-10% service fee (lower than hiver commission)
        return amount * 0.07

    def can_post_task(self) -> bool:
        """Business rule: clients with rating < 2.0 are restricted."""
        return self.rating_as_client.value >= 2.0


@dataclass
class Hiver(User):
    """
    OOP: Inheritance from User.
    Hiver-specific behavior: accepting tasks, earning, leveling up.
    """
    bio: str = ""
    xp_points: int = 0
    level: str = "beginner"   # beginner | experienced | master | legend
    avg_rating: Rating = field(default_factory=lambda: Rating(0.0))
    completed_tasks: int = 0
    is_available_now: bool = False

    def get_role(self) -> str:
        return "hiver"

    def calculate_commission(self, amount: Money) -> Money:
        """
        Polymorphism: Hiver commission depends on level.
        Higher level = lower commission (gamification incentive).
        """
        rates = {
            "beginner":     0.20,
            "experienced":  0.18,
            "master":       0.16,
            "legend":       0.14,
        }
        return amount * rates[self.level]

    def add_xp(self, points: int) -> None:
        """Encapsulation: level-up logic is internal to Hiver."""
        self.xp_points += points
        self._recalculate_level()

    def _recalculate_level(self) -> None:
        thresholds = {"experienced": 100, "master": 500, "legend": 1500}
        for level, threshold in reversed(thresholds.items()):
            if self.xp_points >= threshold:
                self.level = level
                return
        self.level = "beginner"
```

#### SOLID Principles — ALL 5, with comments:
```python
# S — Single Responsibility
# TaskCreationService ONLY creates tasks.
# TaskNotificationService ONLY sends notifications.
# They are separate classes, not combined.
class TaskCreationService:
    """Responsible for: validating task input + persisting task.
    NOT responsible for: sending notifications, calculating prices."""
    ...

class TaskNotificationService:
    """Responsible for: notifying hivers about new tasks.
    NOT responsible for: creating tasks, handling payments."""
    ...


# O — Open/Closed — Strategy Pattern for search sorting
from abc import ABC, abstractmethod

class SearchSortStrategy(ABC):
    """
    Open for extension (add ByPopularity, ByResponseRate),
    closed for modification (existing strategies never change).
    """
    @abstractmethod
    def sort(self, hivers: list[HiverSearchResult]) -> list[HiverSearchResult]:
        ...

class SortByRating(SearchSortStrategy):
    def sort(self, hivers):
        return sorted(hivers, key=lambda h: h.avg_rating, reverse=True)

class SortByDistance(SearchSortStrategy):
    def sort(self, hivers):
        return sorted(hivers, key=lambda h: h.distance_m)

class SortByPrice(SearchSortStrategy):
    def sort(self, hivers):
        return sorted(hivers, key=lambda h: h.min_price)

class SortByRecommended(SearchSortStrategy):
    """Weighted combination of rating, distance, response rate, and boost."""
    def sort(self, hivers):
        def score(h: HiverSearchResult) -> float:
            return (h.avg_rating * 0.4 +
                    (1 / max(h.distance_m, 1)) * 0.3 +
                    h.response_rate * 0.2 +
                    (0.1 if h.is_boosted else 0))
        return sorted(hivers, key=score, reverse=True)


# I — Interface Segregation
# Admin needs both read AND write.
# Public search only needs read.
# Split into two interfaces so search service
# doesn't depend on write methods it never uses.

class IReadableTaskRepository(ABC):
    @abstractmethod
    async def find_by_id(self, task_id: str) -> Task | None: ...
    @abstractmethod
    async def find_nearby(self, location: Location, radius_km: int) -> list[Task]: ...

class IWritableTaskRepository(ABC):
    @abstractmethod
    async def save(self, task: Task) -> Task: ...
    @abstractmethod
    async def update_status(self, task_id: str, status: str) -> None: ...

class ITaskRepository(IReadableTaskRepository, IWritableTaskRepository):
    """Full repository — used by admin and task management services."""
    ...


# D — Dependency Inversion
# CreateTaskUseCase depends on the ITaskRepository INTERFACE,
# never on PostgresTaskRepository directly.
# This allows swapping to an in-memory repo in tests.

class CreateTaskUseCase:
    def __init__(
        self,
        task_repo: ITaskRepository,          # interface, not implementation
        notification_port: INotificationPort, # interface, not Firebase directly
        pricing_service: TaskPricingService,
    ):
        self._task_repo = task_repo
        self._notifications = notification_port
        self._pricing = pricing_service
```

#### Generic Repository — TypeVar and Generic:
```python
# domain/interfaces/repositories.py
from typing import TypeVar, Generic, Protocol
from dataclasses import dataclass

T = TypeVar("T")
ID = TypeVar("ID", str, int)

class IRepository(Generic[T, ID]):
    """
    Generic repository interface.
    OOP: Generics — one interface works for User, Task, Offer, etc.
    Avoids duplicating find_by_id, save, delete for every entity.
    """
    async def find_by_id(self, entity_id: ID) -> T | None: ...
    async def find_all(self, **filters) -> list[T]: ...
    async def save(self, entity: T) -> T: ...
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


# Result type — Railway-oriented error handling
from dataclasses import dataclass
from typing import TypeVar, Generic

T = TypeVar("T")
E = TypeVar("E", bound="AppError")

@dataclass(frozen=True)
class Success(Generic[T]):
    data: T
    success: bool = True

@dataclass(frozen=True)
class Failure(Generic[E]):
    error: E
    success: bool = False

Result = Success[T] | Failure[E]
```

#### Custom Exception Hierarchy:
```python
# domain/errors/domain_errors.py

class AppError(Exception):
    """
    Base error class — all application errors inherit from this.
    OOP: Abstraction — callers catch AppError without knowing specifics.
    """
    def __init__(self, message: str, code: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.is_operational = True  # expected error vs programming bug


class NotFoundError(AppError):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            message=f"{resource} with id '{resource_id}' not found",
            code="NOT_FOUND",
            status_code=404
        )

class TaskNotFoundError(NotFoundError):
    def __init__(self, task_id: str):
        super().__init__("Task", task_id)

class HiverNotFoundError(NotFoundError):
    def __init__(self, hiver_id: str):
        super().__init__("Hiver", hiver_id)


class BusinessRuleViolationError(AppError):
    """Base for all domain rule violations."""
    def __init__(self, message: str, code: str):
        super().__init__(message, code, status_code=422)

class EscrowAlreadyReleasedError(BusinessRuleViolationError):
    def __init__(self, task_id: str):
        super().__init__(
            f"Escrow for task {task_id} has already been released",
            "ESCROW_ALREADY_RELEASED"
        )

class HiverUnavailableError(BusinessRuleViolationError):
    def __init__(self, hiver_id: str):
        super().__init__(
            f"Hiver {hiver_id} is not available for direct booking",
            "HIVER_UNAVAILABLE"
        )

class InsufficientRatingError(BusinessRuleViolationError):
    def __init__(self, client_rating: float):
        super().__init__(
            f"Client rating {client_rating} is too low to post tasks",
            "INSUFFICIENT_CLIENT_RATING"
        )

class UnauthorizedActionError(AppError):
    def __init__(self, action: str):
        super().__init__(
            f"You are not authorized to {action}",
            "UNAUTHORIZED",
            status_code=403
        )

class InvalidEmailError(AppError):
    def __init__(self, email: str):
        super().__init__(f"Invalid email: {email}", "INVALID_EMAIL", 400)
```

#### Context Manager — Python's try-with-resources:
```python
# infrastructure/database/transaction.py
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from shared.logger import logger

@asynccontextmanager
async def db_transaction(session: AsyncSession):
    """
    Async context manager — Python's equivalent of Java try-with-resources.
    Guarantees: transaction is always committed or rolled back.
    Usage: async with db_transaction(session): ...
    
    OOP: Encapsulates transaction lifecycle management.
    Any code using this never needs to write BEGIN/COMMIT/ROLLBACK.
    """
    try:
        yield session
        await session.commit()
        logger.info("transaction.committed")
    except Exception as e:
        await session.rollback()
        logger.error("transaction.rolled_back", error=str(e))
        raise
    finally:
        await session.close()  # always released — equivalent of try-with-resources
```

#### Functional Operations (Python equivalent of Stream API):
```python
# Demonstrate in use cases — never use manual loops where functional is cleaner

# Instead of:
ratings = []
for task in completed_tasks:
    if task.review:
        ratings.append(task.review.rating)
avg = sum(ratings) / len(ratings) if ratings else 0

# Write:
from functools import reduce

ratings = [t.review.rating for t in completed_tasks if t.review]
avg_rating = reduce(lambda acc, r: acc + r, ratings, 0) / len(ratings) if ratings else 0.0

# Filter active boosts:
active_boosts = list(filter(lambda b: b.expires_at > datetime.utcnow(), boosts))

# Map to response DTOs:
offer_responses = list(map(lambda o: OfferResponse.from_domain(o), offers))

# Use generator expressions for memory efficiency with large datasets:
total_earnings = sum(t.hiver_payout for t in transactions if t.status == "released")
```

#### Concurrency — asyncio + threading:
```python
# shared/concurrency/semaphore.py
import asyncio

class BroadcastSemaphore:
    """
    OOP: Encapsulates rate-limiting logic for urgent task broadcasts.
    Prevents overwhelming Firebase FCM with too many simultaneous requests.
    Concurrency: async semaphore controls concurrent access to shared resource.
    """
    def __init__(self, max_concurrent: int = 10):
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def broadcast(self, send_fn, recipients: list) -> list:
        """Send to all recipients, max max_concurrent at a time."""
        async def _send_one(recipient):
            async with self._semaphore:
                return await send_fn(recipient)

        return await asyncio.gather(
            *[_send_one(r) for r in recipients],
            return_exceptions=True  # don't fail all if one fails
        )


# infrastructure/geo/worker.py — CPU-intensive work in thread pool
import asyncio
from concurrent.futures import ThreadPoolExecutor
from math import radians, sin, cos, sqrt, atan2

executor = ThreadPoolExecutor(max_workers=4)

def _haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    CPU-intensive Haversine formula — runs in thread pool,
    not blocking the async event loop.
    Threading: offloads CPU work from async code.
    """
    R = 6371000  # Earth radius in meters
    phi1, phi2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dlambda = radians(lng2 - lng1)
    a = sin(dphi/2)**2 + cos(phi1) * cos(phi2) * sin(dlambda/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

async def calculate_distances_async(
    center_lat: float,
    center_lng: float,
    points: list[tuple[float, float]]
) -> list[float]:
    """Non-blocking: runs Haversine in thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        executor,
        lambda: [_haversine_distance(center_lat, center_lng, lat, lng)
                 for lat, lng in points]
    )
```

#### Design Patterns — 5 patterns with documented justification:
```python
# 1. REPOSITORY PATTERN
# Why: Decouples use cases from PostgreSQL.
# Without it: use cases import SQLAlchemy directly → untestable.
# With it: tests inject InMemoryTaskRepository, no DB needed.
class PostgresTaskRepository(ITaskRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def find_nearby(self, location: Location, radius_km: int) -> list[Task]:
        # Uses PostGIS ST_DWithin — the only place SQL leaks into infra layer
        ...


# 2. STRATEGY PATTERN — already shown above in SortByRating/Distance/Price
# Why: New sort algorithm = new class, zero changes to SearchService.
# At runtime: client passes sort=rating → SearchService uses SortByRating.


# 3. OBSERVER PATTERN — Event bus
# Why: TaskAccepted event triggers 3 side effects (notification, escrow, chat).
# Without Observer: CreateTaskUseCase would import NotificationService,
# EscrowService, ChatService — huge coupling.

from typing import Callable, Awaitable
from dataclasses import dataclass

@dataclass
class DomainEvent:
    event_type: str
    payload: dict

class EventBus:
    """
    Observer Pattern: publishers emit events, observers react.
    OOP: Decouples event producers from consumers.
    """
    def __init__(self):
        self._handlers: dict[str, list[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable) -> None:
        self._handlers.setdefault(event_type, []).append(handler)

    async def publish(self, event: DomainEvent) -> None:
        for handler in self._handlers.get(event.event_type, []):
            await handler(event)

# Usage:
event_bus.subscribe("task.accepted", escrow_handler)
event_bus.subscribe("task.accepted", notification_handler)
event_bus.subscribe("task.accepted", chat_initializer)
await event_bus.publish(DomainEvent("task.accepted", {"task_id": task.id}))


# 4. FACTORY PATTERN — Smart questions per vertical
# Why: Each vertical has different required fields.
# Without Factory: 5 if/elif blocks scattered across codebase.

class TaskFactory:
    """
    Factory Pattern: creates Task with correct validation per vertical.
    OOP: Encapsulates construction complexity.
    """
    _builders: dict[str, type] = {}

    @classmethod
    def register(cls, vertical: str):
        def decorator(builder_class):
            cls._builders[vertical] = builder_class
            return builder_class
        return decorator

    @classmethod
    def create(cls, vertical: str, data: dict) -> Task:
        builder = cls._builders.get(vertical)
        if not builder:
            raise ValueError(f"Unknown vertical: {vertical}")
        return builder(data).build()

@TaskFactory.register("home")
class HomeTaskBuilder:
    def __init__(self, data): self.data = data
    def build(self) -> Task:
        # Validates home-specific fields: property_type, size_sqm, etc.
        ...

@TaskFactory.register("learn")
class LearnTaskBuilder:
    def __init__(self, data): self.data = data
    def build(self) -> Task:
        # Validates learn-specific fields: subject, student_age, etc.
        ...


# 5. ADAPTER PATTERN — Payment methods
# Why: Stripe and PayPal have completely different APIs.
# Without Adapter: payment logic leaks into use cases.

class IPaymentPort(ABC):
    @abstractmethod
    async def hold_payment(self, amount: Money, customer_id: str) -> str: ...
    @abstractmethod
    async def release_payment(self, payment_id: str) -> None: ...
    @abstractmethod
    async def refund_payment(self, payment_id: str, amount: Money) -> None: ...

class StripeAdapter(IPaymentPort):
    """Adapts Stripe API to IPaymentPort interface."""
    def __init__(self, stripe_client):
        self._stripe = stripe_client

    async def hold_payment(self, amount: Money, customer_id: str) -> str:
        intent = await self._stripe.payment_intents.create(
            amount=int(amount.value * 100),  # Stripe uses cents
            currency="bgn",
            customer=customer_id,
            capture_method="manual"  # hold without capturing = simulated escrow
        )
        return intent.id
```

---

## PHASE 3 — Database Migrations (Third Commit)

### Alembic Setup:
```python
# alembic/env.py — async migrations
from alembic import context
from sqlalchemy.ext.asyncio import async_engine_from_config
from src.infrastructure.database.models import Base

target_metadata = Base.metadata
```

### Migration Files — complete sequence:
```
alembic/versions/
├── 001_create_extensions.py         # PostGIS, uuid-ossp, pgcrypto
├── 002_create_users_table.py
├── 003_create_clients_hivers.py
├── 004_create_skills.py
├── 005_create_tasks.py
├── 006_create_offers.py
├── 007_create_transactions.py
├── 008_create_reviews.py
├── 009_create_messages.py
├── 010_create_disputes.py
├── 011_create_boosts.py
├── 012_create_notification_log.py
├── 013_create_all_indexes.py
├── 014_create_plpgsql_functions.py  # triggers + stored functions
└── 015_create_views.py              # hiver_earnings_monthly view
```

Each migration has both `upgrade()` and `downgrade()` functions.
Never use `op.execute("DROP TABLE")` in upgrade — always reversible.

### SQLAlchemy Models (infrastructure layer — NOT domain entities):
```python
# infrastructure/database/models/task_model.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DECIMAL, ARRAY, Text
from geoalchemy2 import Geography
import uuid

class TaskModel(Base):
    __tablename__ = "tasks"

    id:           Mapped[str] = mapped_column(
                    String, primary_key=True,
                    default=lambda: str(uuid.uuid4()))
    client_id:    Mapped[str] = mapped_column(String, ForeignKey("clients.user_id"))
    hiver_id:     Mapped[str | None] = mapped_column(String, ForeignKey("hivers.user_id"))
    vertical:     Mapped[str] = mapped_column(String(20))
    subcategory:  Mapped[str] = mapped_column(String(50))
    status:       Mapped[str] = mapped_column(String(20), default="open")
    budget_min:   Mapped[float | None] = mapped_column(DECIMAL(10, 2))
    budget_max:   Mapped[float | None] = mapped_column(DECIMAL(10, 2))
    is_urgent:    Mapped[bool] = mapped_column(Boolean, default=False)
    location_point: Mapped[object | None] = mapped_column(
                    Geography(geometry_type="POINT", srid=4326))
    location_display: Mapped[str | None] = mapped_column(String(100))
    smart_answers: Mapped[dict | None] = mapped_column(JSONB)
    image_urls:   Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    created_at:   Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at:   Mapped[datetime] = mapped_column(
                    default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client:  Mapped["ClientModel"] = relationship(back_populates="tasks")
    offers:  Mapped[list["OfferModel"]] = relationship(back_populates="task")
    messages: Mapped[list["MessageModel"]] = relationship(back_populates="task")
```

### PL/pgSQL Triggers and Functions — included in migration 014:

**Trigger 1:** Auto-update hiver avg_rating and completed_tasks when review revealed.
**Trigger 2:** Reveal both reviews when both parties submit (bidirectional reveal).
**Trigger 3:** updated_at auto-timestamp on all tables.
**Function:** `find_hivers_in_radius(lat, lng, radius_km, vertical)` — PostGIS radius search.
**View:** `hiver_earnings_monthly` — window functions with RANK() and running totals.

Include EXPLAIN ANALYZE output as SQL comments on all complex queries:
```sql
-- Performance note (EXPLAIN ANALYZE on 10k rows):
-- Before index: Seq Scan, cost=850.00, actual time=45ms
-- After GIST index: Index Scan, cost=12.50, actual time=0.3ms
-- Decision: 150x speedup justifies index maintenance overhead
```

---

## PHASE 4 — API Layer (Fourth Commit)

### FastAPI Router Structure:
```python
# infrastructure/http/routers/tasks.py
from fastapi import APIRouter, Depends, Query, Path
from typing import Annotated

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])
# NOTE: /api/v1/ prefix — API versioning for РС grade

@router.post("/", status_code=201, response_model=TaskResponse,
             summary="Create a new task",
             description="Client posts a task with smart answers per vertical.")
async def create_task(
    body: CreateTaskRequest,                     # Pydantic validates input
    use_case: Annotated[CreateTaskUseCase, Depends(get_create_task_use_case)],
    current_user: Annotated[Client, Depends(get_current_client)],
) -> TaskResponse:
    result = await use_case.execute(body, current_user.id)
    if not result.success:
        raise HTTPException(status_code=result.error.status_code,
                           detail=result.error.message)
    return TaskResponse.from_domain(result.data)


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task(
    task_id: Annotated[str, Path(description="UUID of the task")],
    ...
): ...


@router.get("/nearby", response_model=PaginatedResult[TaskSummaryResponse])
async def get_nearby_tasks(
    lat: Annotated[float, Query(ge=-90, le=90)],
    lng: Annotated[float, Query(ge=-180, le=180)],
    radius_km: Annotated[int, Query(ge=1, le=20)] = 5,
    vertical: str | None = None,
    ...
): ...
```

### Dependency Injection with dependency-injector:
```python
# shared/container.py
from dependency_injector import containers, providers
from dependency_injector.wiring import inject, Provide

class Container(containers.DeclarativeContainer):
    """
    DI Container: wires all dependencies.
    OOP + SOLID D: nothing creates its own dependencies.
    """
    # Infrastructure
    db_pool = providers.Singleton(create_async_engine, DATABASE_URL)
    redis_client = providers.Singleton(aioredis.from_url, REDIS_URL)

    # Repositories (depend on interfaces, inject implementations)
    task_repo = providers.Factory(PostgresTaskRepository, session=db_pool)
    hiver_repo = providers.Factory(PostgresHiverRepository, session=db_pool)

    # Ports (adapters)
    payment_port = providers.Singleton(StripeAdapter, stripe_client=stripe)
    notification_port = providers.Singleton(FirebaseAdapter)
    storage_port = providers.Singleton(SupabaseStorageAdapter)

    # Use cases (inject repositories and ports — never implementations)
    create_task_use_case = providers.Factory(
        CreateTaskUseCase,
        task_repo=task_repo,
        notification_port=notification_port,
        pricing_service=providers.Factory(TaskPricingService),
    )
```

### Centralized Error Handling:
```python
# infrastructure/http/middleware/error_handler.py
from fastapi import Request
from fastapi.responses import JSONResponse
from domain.errors.domain_errors import AppError
from shared.logger import logger

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """
    Centralized error handler — no try/except scattered in controllers.
    Operational errors (404, 422) → clean JSON response.
    Programming errors → 500 + log full stack trace.
    """
    if not exc.is_operational:
        logger.error("unexpected_error",
                     path=request.url.path,
                     error=str(exc),
                     exc_info=True)
        return JSONResponse(status_code=500,
                           content={"error": "Internal server error"})

    logger.warning("operational_error",
                   code=exc.code,
                   message=exc.message,
                   path=request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.code, "message": exc.message}
    )
```

---

## PHASE 5 — Tests (Fifth Commit)

### Test Structure:
```python
# tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture(scope="session")
async def test_db():
    """Real PostgreSQL test database — separate from development."""
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def client(app):
    """HTTP test client — no real server needed."""
    async with AsyncClient(transport=ASGITransport(app=app),
                           base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_task_repo():
    """In-memory repository — no DB needed for unit tests."""
    return InMemoryTaskRepository()
```

```python
# tests/unit/application/test_create_task_use_case.py

class TestCreateTaskUseCase:
    async def test_creates_task_successfully(self, mock_task_repo, mock_notifications):
        # Arrange
        use_case = CreateTaskUseCase(
            task_repo=mock_task_repo,
            notification_port=mock_notifications,
            pricing_service=TaskPricingService()
        )
        command = CreateTaskCommand(vertical="home", subcategory="cleaning", ...)

        # Act
        result = await use_case.execute(command, client_id="test-client")

        # Assert
        assert result.success
        assert result.data.status == "open"
        assert mock_notifications.was_called_with("task.created")

    async def test_rejects_low_rated_client(self, mock_task_repo):
        """Edge case: client with rating < 2.0 cannot post tasks."""
        low_rated_client = Client(rating_as_client=Rating(1.5), ...)
        result = await use_case.execute(command, client_id=low_rated_client.id)

        assert not result.success
        assert isinstance(result.error, InsufficientRatingError)

    async def test_urgent_task_sets_expiry(self):
        """Urgent tasks must have auto-expiry timestamp."""
        ...
```

Target: **>80% coverage** including edge cases.
Run: `pytest --cov=src --cov-report=html --cov-fail-under=80`

---

## VIRTUALIZATION — Targeting Отличен (6)

### Dockerfile — Multi-stage (final image < 150MB):
```dockerfile
# backend/Dockerfile

# Stage 1: Install dependencies only
FROM python:3.12-slim AS deps
WORKDIR /app
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Stage 2: Production image — minimal
FROM python:3.12-slim AS production
WORKDIR /app

# Security: non-root user
RUN groupadd -r hiver && useradd -r -g hiver hiver

# Copy only what's needed from deps stage
COPY --from=deps /app/.venv .venv
COPY src/ src/

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

USER hiver
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Terraform — Modules (not monolithic):
```hcl
# infra/terraform/modules/networking/main.tf
resource "aws_vpc" "hiver" {
  cidr_block           = var.cidr_block
  enable_dns_hostnames = true
  tags = { Name = "hiver-${var.environment}" }
}

# infra/terraform/environments/prod/main.tf
module "networking" {
  source      = "../../modules/networking"
  cidr_block  = "10.0.0.0/16"
  environment = "prod"
}

module "database" {
  source      = "../../modules/database"
  vpc_id      = module.networking.vpc_id
  subnet_ids  = module.networking.private_subnet_ids
}

# Remote state — prevents conflicts between team members
terraform {
  backend "s3" {
    bucket         = "hiver-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "eu-central-1"
    dynamodb_table = "hiver-terraform-locks"  # prevents concurrent applies
    encrypt        = true
  }
}
```

### Helm Chart — Zero-downtime deployment:
```yaml
# infra/k8s/charts/hiver/values.yaml
replicaCount: 2

image:
  repository: hiver/backend
  tag: latest
  pullPolicy: IfNotPresent

strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0     # zero-downtime: always at least 2 pods running

resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

### GitHub Actions CI/CD:
```yaml
# .github/workflows/ci.yml
name: CI

on:
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run ruff linter
        run: ruff check src/
      - name: Run mypy type checker
        run: mypy src/ --strict

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgis/postgis:16-3.4-alpine
        env: { POSTGRES_PASSWORD: test, POSTGRES_DB: hiver_test }
        options: --health-cmd pg_isready --health-interval 10s
    steps:
      - uses: actions/checkout@v4
      - name: Run tests with coverage
        run: pytest --cov=src --cov-report=xml --cov-fail-under=80
      - name: Upload coverage report
        uses: codecov/codecov-action@v4

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Dependency vulnerability scan
        run: pip-audit
      - name: Secret detection
        uses: trufflesecurity/trufflehog@main

  docker:
    needs: [lint, test, security]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build multi-stage image
        run: docker build --target production -t hiver/backend:${{ github.sha }} .
      - name: Check image size
        run: |
          SIZE=$(docker image inspect hiver/backend:${{ github.sha }} \
                 --format='{{.Size}}')
          echo "Image size: $((SIZE/1024/1024))MB"

# .github/workflows/cd.yml — deploys on merge to main
# Helm upgrade with --wait and Slack/Discord notification on success/failure
```

### Observability:
```python
# shared/metrics.py
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Counter, Histogram, Gauge

tasks_created = Counter(
    "hiver_tasks_created_total",
    "Tasks created",
    ["vertical", "is_urgent"]
)

escrow_held_bgn = Gauge(
    "hiver_escrow_held_bgn",
    "Total BGN currently held in escrow"
)

search_duration = Histogram(
    "hiver_search_duration_seconds",
    "Hiver search query duration",
    ["vertical", "sort_strategy"],
    buckets=[0.01, 0.05, 0.1, 0.3, 0.5, 1.0]
)
```

Grafana dashboards provisioned from JSON files in `infra/grafana/dashboards/`:
- API performance (p50/p95/p99 per endpoint)
- Business metrics (tasks/hour, escrow balance, active hivers)
- Infrastructure (CPU, memory, DB pool utilization)

Prometheus alerts (in `infra/prometheus/alerts.yml`):
- Error rate > 5% for 5 minutes
- DB connection pool > 80%
- Escrow auto-release job not run in 2 hours

---

## STRUCTURED LOGGING:
```python
# shared/logger.py
import structlog

logger = structlog.get_logger()

# Usage — always structured, never f-strings in logs:
logger.info("task.created",
            task_id=task.id,
            client_id=client_id,
            vertical=task.vertical,
            duration_ms=elapsed)

logger.error("escrow.release_failed",
             task_id=task_id,
             error=str(e),
             exc_info=True)

# Log levels: DEBUG (dev), INFO (operations), WARNING (soft errors), ERROR (failures)
```

---

## AI DECISIONS LOG — Mandatory for Отличен:

Maintain `docs/ai-decisions.md`. Example format:
```markdown
### 2024-01-15 — Context manager for DB transactions
**Tool:** Claude
**Prompt:** "Generate a Python async context manager for PostgreSQL transactions"
**Generated:** Basic try/except/finally with session.commit/rollback
**Accepted:** Yes — the pattern is correct
**Modified:** Added structlog logging, specific exception types,
              retry logic for serialization failures
**Rejected approach:** AI suggested using SQLAlchemy's built-in
             session.begin() context manager — rejected because
             it hides rollback behavior and makes testing harder
**Learned:** PostgreSQL SERIALIZABLE isolation vs READ COMMITTED trade-offs
```

---

## WHAT CLAUDE CODE SHOULD DO:

**Phase 1 — Stop after generating:**
- Folder structure (empty `__init__.py` files)
- pyproject.toml with all dependencies
- .env.example with documentation
- docker-compose.yml
- Dockerfile (multi-stage)
- .gitignore
- .pre-commit-config.yaml
- README.md skeleton

**Phase 2 — Stop after generating:**
- All domain entities with full OOP patterns
- All custom exceptions
- All repository interfaces
- All value objects (Money, Location, Rating, WorkRadius)

**Phase 3 — Stop after generating:**
- All 15 Alembic migrations with upgrade() and downgrade()
- All SQLAlchemy models
- PL/pgSQL triggers and functions
- Seed data scripts

**Phase 4 — Stop after generating:**
- All FastAPI routers
- DI container wiring
- All use cases
- All repository implementations
- Error handling middleware

**Phase 5 — Stop after generating:**
- Unit tests (>60% coverage milestone)
- Integration tests
- CI/CD GitHub Actions workflows
- Terraform module skeletons
- Helm chart
- Prometheus + Grafana config

Do NOT proceed to the next phase without confirmation.
After each phase, summarize: what was created, what decisions were made,
and what the student should review and understand before the next phase.
