# Hiver — Defence Deep-Dive: Databases (БД) & OOP (ООП)

Everything in this file is in the code — file paths are given so you can open the source while you
talk. Two parts: **Databases** then **OOP**. Each ends with likely examiner questions + answers.

---

# PART 1 — DATABASES (БД)

## 1.1 The stack, in one breath

- **PostgreSQL 16 + PostGIS**, hosted on **Supabase** as *managed Postgres* (reached through the
  pgbouncer transaction pooler). Supabase is just the host — we do **not** use its auto data API.
- Schema is built and versioned with **Alembic** — **22 migrations** (`001` → `022`).
- Access from the backend is **async SQLAlchemy 2.0 + asyncpg**, through the **Repository pattern**.
- Beyond plain tables we have: **PostGIS geo-search** (a PL/pgSQL stored function), **3 triggers**,
  a **window-function view**, **GIST / partial / composite indexes**, and **Row-Level Security**.

Files:
- Models (ORM tables): `backend/src/infrastructure/database/models/*.py`
- Migrations: `backend/src/infrastructure/database/migrations/versions/001…022_*.py`
- Repositories (SQL/PostGIS): `backend/src/infrastructure/database/repositories/*.py`
- Seed data: `backend/src/infrastructure/database/seed.py`

## 1.2 Schema — 14 tables

One model file per table in `…/database/models/`:

| Table | Model file | Purpose |
|---|---|---|
| `users` | `user_model.py` | shared account row (email, password hash, OAuth) |
| `clients` | `client_model.py` | client-side profile (1-to-1 with users) |
| `hivers` | `hiver_model.py` | hiver profile + **`location_point Geography(POINT,4326)`** |
| `skills` / `hiver_skills` | `skill_model.py` | skills catalogue + M-to-N link to hivers |
| `tasks` | `task_model.py` | the job; **`location_point Geography(POINT)`**, `JSONB smart_answers`, `ARRAY image_urls` |
| `offers` | `offer_model.py` | a hiver's bid on a task |
| `transactions` | `transaction_model.py` | **escrow** row (status, gross, fee, payout, `released_at`) |
| `reviews` | `review_model.py` | blind two-way reviews (`is_revealed`) |
| `messages` | `message_model.py` | task chat |
| `disputes` | `dispute_model.py` | dispute opened against escrow |
| `boosts` | `boost_model.py` | paid hiver visibility |
| `notification_log` | `notification_log_model.py` | in-app notifications |
| `favorites` | `favorite_model.py` | saved tasks/hivers |

**Normalization:** the schema is **3NF**. Two *documented denormalizations* on `hivers` for read
performance — `avg_rating` and `completed_tasks` — kept correct by a trigger (see §1.5), so we never
recompute them with an aggregate on every profile view.

## 1.3 Migrations — 22 chained Alembic steps

Alembic = versioned schema. Each migration has a `revision`, a `down_revision` (forming a chain
`001→002→…→022`), and `upgrade()` / `downgrade()`. `alembic upgrade head` applies everything;
`downgrade` rolls back. **Migrations are the single source of truth** — we never hand-edit tables.

Notable ones:
- `001_create_extensions` — `CREATE EXTENSION postgis` (+ uuid/pgcrypto).
- `005_create_tasks` — the `tasks` table incl. the PostGIS `location_point` (added via raw
  `op.execute()` SQL because GeoAlchemy2's `Geography` type can't be used inside
  `op.create_table()`).
- `013_create_all_indexes` — every GIST / partial / composite index (see §1.7).
- `014_create_plpgsql_functions` — the 3 triggers + the `find_hivers_in_radius` function (§1.4–1.5).
- `015_create_views` — the `hiver_earnings_monthly` window-function view (§1.6).
- `017_enable_rls_and_secure_view` — Row-Level Security (§1.8).
- `018` budget-range CHECK, `019` dual-role backfill, `021` favorites, `022` task featured-until.

> Gotcha we can defend: a partial-index predicate **must be `IMMUTABLE`** — you can't put `NOW()` in
> a `WHERE`. We filter on time at *query* time instead.

## 1.4 PostGIS geospatial search (the БД showpiece)

`hivers.location_point` and `tasks.location_point` are **`Geography(POINT, SRID 4326)`** columns —
SRID 4326 = WGS-84 GPS coordinates. Coordinates come from **Google Places** (real addresses).

The proximity search is a **PL/pgSQL stored function** (`014_create_plpgsql_functions.py`):

```sql
CREATE OR REPLACE FUNCTION find_hivers_in_radius(
    center_lat DOUBLE PRECISION, center_lng DOUBLE PRECISION,
    radius_km INT, p_vertical VARCHAR DEFAULT NULL)
RETURNS TABLE (user_id VARCHAR, distance_m DOUBLE PRECISION,
               avg_rating DECIMAL, level VARCHAR, is_available BOOLEAN) AS $$
BEGIN
  RETURN QUERY
  SELECT h.user_id,
         ST_Distance(h.location_point::geography,
                     ST_MakePoint(center_lng, center_lat)::geography) AS distance_m,
         h.avg_rating, h.level, h.is_available_now
  FROM hivers h
  WHERE h.location_point IS NOT NULL
    AND h.is_available_now = true
    AND ST_DWithin(h.location_point::geography,
                   ST_MakePoint(center_lng, center_lat)::geography,
                   radius_km * 1000)                         -- km → metres
    AND (p_vertical IS NULL OR EXISTS (                      -- optional category filter
        SELECT 1 FROM hiver_skills hs JOIN skills s ON s.id = hs.skill_id
        WHERE hs.hiver_id = h.user_id AND s.vertical = p_vertical))
  ORDER BY distance_m ASC;
END; $$ LANGUAGE plpgsql;
```

Key functions to name-drop: **`ST_DWithin`** (true/false "within X metres", uses the index),
**`ST_Distance`** (exact metres for sorting), **`ST_MakePoint`** (build the search point),
`::geography` (great-circle metres, not planar degrees). Called from
`PostgresHiverRepository.find_available_near()` in `repositories/user_repository.py`.

## 1.5 Triggers (3 PL/pgSQL triggers — `014_create_plpgsql_functions.py`)

1. **`trg_*_updated_at`** — `BEFORE UPDATE` on `users/tasks/offers/transactions`; `fn_set_updated_at()`
   stamps `NEW.updated_at = NOW()`. (One function, attached to four tables.)
2. **`trg_reveal_reviews`** — `AFTER INSERT ON reviews`; `fn_reveal_reviews()` counts reviews for the
   task and, once **both** parties have submitted (`count >= 2`), flips `is_revealed = true` on both.
   This is the **blind-review** mechanism — you can't see the other side's review until you've written
   yours, so nobody retaliates.
3. **`trg_update_hiver_rating`** — `AFTER UPDATE OF is_revealed ON reviews`; when a review about a
   hiver becomes revealed, `fn_update_hiver_rating()` recomputes the hiver's `avg_rating`, bumps
   `completed_tasks`, `review_count`, `xp_points (+10)`, and recalculates `level`
   (beginner/experienced/master/legend by XP). This keeps the denormalized columns correct.

```sql
-- blind reveal (excerpt)
SELECT COUNT(*) INTO review_count FROM reviews WHERE task_id = NEW.task_id;
IF review_count >= 2 THEN
  UPDATE reviews SET is_revealed = true WHERE task_id = NEW.task_id;
END IF;
```

## 1.6 Window-function view — `hiver_earnings_monthly` (`015_create_views.py`)

Per-hiver monthly earnings, with **three different window functions**:

```sql
CREATE OR REPLACE VIEW hiver_earnings_monthly AS
SELECT t.hiver_id,
       DATE_TRUNC('month', t.released_at)  AS month,
       COUNT(*)                            AS tasks_completed,
       SUM(t.hiver_payout)                 AS monthly_earnings,
       RANK()  OVER (PARTITION BY DATE_TRUNC('month', t.released_at)
                     ORDER BY SUM(t.hiver_payout) DESC)          AS rank_in_month,
       SUM(SUM(t.hiver_payout)) OVER (PARTITION BY t.hiver_id
                     ORDER BY DATE_TRUNC('month', t.released_at)
                     ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_total,
       AVG(SUM(t.hiver_payout)) OVER (PARTITION BY t.hiver_id
                     ORDER BY DATE_TRUNC('month', t.released_at)
                     ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)         AS rolling_3mo_avg
FROM transactions t
WHERE t.status = 'released' AND t.released_at IS NOT NULL
GROUP BY t.hiver_id, DATE_TRUNC('month', t.released_at);
```

Talking points: **`RANK() OVER (PARTITION BY … ORDER BY …)`** = leaderboard position per month;
**`SUM(SUM(...)) OVER (… UNBOUNDED PRECEDING …)`** = running career total; **`AVG(SUM(...)) OVER
(… 2 PRECEDING …)`** = 3-month rolling average via a frame clause. Note the **window aggregate over a
GROUP BY aggregate** (`SUM(SUM(...))`) — a genuinely advanced SQL feature.

## 1.7 Indexes (`013_create_all_indexes.py`)

- **GIST** index on `location_point` — what makes `ST_DWithin` fast (≈150× vs a sequential scan).
- **Partial** indexes — e.g. only urgent/active tasks, only active boosts (smaller, hotter index).
- **Composite** indexes — e.g. `(status, created_at)`, `(client_id, status)` for the common filters.

## 1.8 Row-Level Security (`017_enable_rls_and_secure_view.py`)

**Why:** Supabase auto-exposes the whole `public` schema over PostgREST with the public `anon` key —
an open door we never use. Its linter flags 15 ERROR findings (RLS off on 14 tables + a
SECURITY DEFINER view).

**Fix:**
1. `ALTER TABLE … ENABLE ROW LEVEL SECURITY` on every public table. **With no policies attached this
   is "default-deny"** for the anon/authenticated API roles → the public API is shut. Our backend
   connects as the **table owner (BYPASSRLS)**, so the app is completely unaffected.
2. Recreate the earnings view `WITH (security_invoker = on)` so it runs with the *caller's* rights and
   respects RLS instead of leaking earnings past it (Postgres 15+, which Supabase runs).

This is defence-in-depth: even if someone hit the DB directly, they get nothing.

## 1.9 How the app talks to the DB (pooler-safe async)

- `session.py` builds an **async engine** (`asyncpg`). When `DATABASE_USE_POOLER=true` it disables
  the prepared-statement cache and uses `NullPool`, because pgbouncer in **transaction mode** can't
  keep server-side prepared statements — otherwise you'd get "prepared statement does not exist".
- Repositories translate between domain entities and rows; PostGIS bits use **raw SQL via
  `text()`**, and writes build the point with a `WKTElement` / `ST_MakePoint` (no shapely dependency).

## 1.10 БД — likely questions & answers

- **"Why PostgreSQL and not Supabase's API?"** We need PostGIS, full SQL control (PL/pgSQL triggers,
  stored functions, window-function views) and Alembic migrations. Supabase is only the managed
  *host* + Storage; its auto API is locked off with RLS.
- **"Show a stored procedure."** `find_hivers_in_radius` (§1.4) — PL/pgSQL, returns a table.
- **"Show a trigger."** Blind-review reveal / rating recompute (§1.5).
- **"Show a view with window functions."** `hiver_earnings_monthly` (§1.6) — RANK + running total +
  rolling average.
- **"Is it normalized?"** 3NF, with two *documented* denormalizations kept consistent by a trigger.
- **"How do you migrate?"** Alembic chain `001→022`; `upgrade head`; never edit applied migrations.

---

# PART 2 — OBJECT-ORIENTED PROGRAMMING (ООП)

## 2.1 The frame: Clean Architecture

Four layers, dependencies point **inward only**:

```
HTTP (FastAPI routers/middleware)
        ↓
Application (use cases + DTOs)
        ↓
Domain (entities, value objects, interfaces)   ← pure Python, ZERO framework imports
        ↑
Infrastructure (DB, storage, payments) ── implements the domain's interfaces
```

The **domain** (`backend/src/domain/`) imports no SQLAlchemy/FastAPI/Stripe. That's what makes the
business rules unit-testable and the providers swappable.

## 2.2 Inheritance + Polymorphism — `domain/entities/user.py`

`User` is an **abstract base class (`ABC`)** with two **abstract methods**; `Client` and `Hiver`
inherit and implement them differently — textbook **polymorphism**:

```python
@dataclass
class User(ABC):
    @abstractmethod
    def get_role(self) -> str: ...
    @abstractmethod
    def calculate_commission(self, amount: Money) -> Money: ...

class Client(User):
    def get_role(self): return "client"
    def calculate_commission(self, amount): return amount * 0.07   # flat 7% service fee

class Hiver(User):
    def get_role(self): return "hiver"
    def calculate_commission(self, amount):                        # depends on LEVEL
        rates = {"beginner":0.20,"experienced":0.18,"master":0.16,"legend":0.14}
        return amount * rates[self.level]
```

- **Abstraction/Encapsulation:** password logic lives inside `User.verify_password()`; the hash is a
  protected `_password_hash` behind a read-only `password_hash` property.
- **Encapsulated behaviour:** `Hiver.add_xp()` → `_recalculate_level()` (level-up is internal);
  `Hiver.is_within_radius()` uses the `WorkRadius` + `Location` value objects.
- **Liskov:** anywhere a `User` is expected, a `Client` or `Hiver` works — `calculate_commission`
  has the same signature in both.

## 2.3 Encapsulation via Value Objects — `domain/value_objects/`

Immutable (`@dataclass(frozen=True)`), always-valid little objects — no raw floats/strings leak into
the domain:

- **`Money`** (`money.py`) — `Decimal` with currency; validates non-negative, quantizes to 2 dp,
  overloads `+ - * > >= < <=`, refuses cross-currency math. Arithmetic returns **new** `Money`.
- **`Rating`** (`rating.py`) — 0.0–5.0, `is_acceptable()` (≥2.0 business rule),
  `recalculate(count, new)` returns a new rolling-average `Rating`.
- **`WorkRadius`** (`work_radius.py`) — constrained to tiers `(1,2,5,10,15,20)`; `covers(distance)`.
- **`Location`** (`location.py`) — lat/lng (WGS-84), Haversine `distance_to_km()` inside the object.

Why it matters: validation can't be forgotten (it's in `__post_init__`), and immutability means no
spooky action-at-a-distance.

## 2.4 SOLID — one concrete example each

- **S (Single responsibility):** every use case does one thing — `CreateTaskUseCase`,
  `ReleaseEscrowUseCase`, `DeleteTaskImageUseCase` (`application/use_cases/**`).
- **O (Open/closed):** add a new payment or storage provider by writing an adapter — no edits to use
  cases.
- **L (Liskov):** any `IStoragePort` adapter (Supabase, a mock) is substitutable; `Client`/`Hiver` for
  `User`.
- **I (Interface segregation):** small focused ports — `IPaymentPort`, `IStoragePort`,
  `INotificationPort`, `IGeoPort`, `ITaskRepository` (`domain/interfaces/`).
- **D (Dependency inversion):** use cases depend on those **interfaces**, never on the Stripe SDK or
  SQLAlchemy. Infrastructure implements them. (See `IPaymentPort` docstring — it literally says this.)

## 2.5 Design Patterns (with file pointers)

| Pattern | Where | What it does |
|---|---|---|
| **Repository** | `domain/interfaces/repositories.py` + `…/repositories/*_repository.py` | hide SQL/PostGIS behind `ITaskRepository`/`IHiverRepository`; generic `PaginatedResult[T]` |
| **Adapter** | `infrastructure/payments/`, `…/storage/`, `…/notifications/` | `MockPaymentAdapter`/`StripeAdapter` ⟶ `IPaymentPort`; `SupabaseStorageAdapter` ⟶ `IStoragePort` |
| **Strategy** | `payment_factory`, `storage_factory` | swap the concrete strategy at runtime by config |
| **Factory** | `payments/payment_factory.py`, `storage/storage_factory.py`, `domain/services/task_factory.py` | build the right object; app layer never sees the concrete class |
| **Builder** | `domain/services/task_factory.py` | vertical-specific `TaskBuilder`s assemble a `Task` |
| **Observer** | `domain/services/event_bus.py` | publish/subscribe domain events → in-app notifications |
| **Value Object** | `domain/value_objects/*` | immutable, self-validating (§2.3) |
| **State machine** | `Task.status` transitions in `domain/entities/task.py` | open→accepted→in_progress→completed / cancelled / disputed |

**Adapter / Dependency-Inversion (`domain/interfaces/ports.py`):**
```python
class IPaymentPort(ABC):                       # the domain owns this interface
    async def hold_payment(self, amount: Money, customer_id: str) -> str: ...
    async def release_payment(self, payment_intent_id: str) -> None: ...
    async def refund_payment(self, payment_intent_id: str, amount: Money) -> None: ...
```

**Factory (`payment_factory.py`)** — *one line to go live*; the application never knows which adapter
it got:
```python
def get_payment_port() -> IPaymentPort:
    key = settings.stripe_secret_key or ""
    if _is_real_stripe_key(key):           # real "sk_…" key (not a dummy)?
        return StripeAdapter(stripe.StripeClient(key))
    return MockPaymentAdapter()            # functional mock — escrow works with no account
```

**Builder + Factory (`task_factory.py`)** — pick a builder per vertical, then build:
```python
_BUILDERS = {"home": HomeTaskBuilder, "learn": LearnTaskBuilder,
             "tech": TechTaskBuilder, "care": GenericTaskBuilder, ...}

class TaskFactory:
    @classmethod
    def create(cls, data: TaskCreateData) -> Task:
        builder = _BUILDERS.get(data.vertical, GenericTaskBuilder)
        return builder(data).build()
```

**Observer (`event_bus.py`)** — decouples "something happened" from "notify the user":
```python
class EventBus:                                  # Observer
    def subscribe(self, event_type, handler): ...
    async def publish(self, event):
        for h in self._handlers.get(event.event_type, []): await h(event)
```
The HTTP layer injects a request-scoped bus whose subscriber writes to `notification_log`; **unit
tests construct use cases with no bus and the calls become no-ops** — clean decoupling.

## 2.6 Custom exception hierarchy — `domain/errors/domain_errors.py`

A polymorphic tree where each class carries an **HTTP status code**, so one middleware turns any
domain error into the right JSON response:

```
AppError(message, code, status_code)
├── NotFoundError (404)            → TaskNotFound, HiverNotFound, ClientNotFound,
│                                     OfferNotFound, ReviewNotFound, DisputeNotFound, TransactionNotFound
├── BusinessRuleViolationError (422) → EscrowAlreadyReleased, HiverUnavailable, InsufficientRating,
│                                     TaskAlreadyAccepted, OfferAlreadyExists, CannotOfferOnOwnTask,
│                                     ReviewAlreadySubmitted, InvalidBudgetRange, MissingSmartAnswer, …
├── AuthError (401/403)            → InvalidCredentials, ExpiredToken, UnauthorizedAction
└── ValidationError (422)          → InvalidValueObject / InvalidEmail
```

The error-handler middleware (`infrastructure/http/middleware/error_handler.py`) catches `AppError`
and returns `{message, code}` with `err.status_code`; unexpected exceptions become a 500.

## 2.7 Generics & functional style

- **`PaginatedResult[T]`** and the repository interfaces are **generic** — one shape for tasks,
  offers, hivers, no duplication (`domain/interfaces/repositories.py`).
- DTO mapping uses **list comprehensions** rather than manual loops (e.g. `ListClientTasksUseCase`).
- Async **context manager** `async with db_transaction(...)` = Python's try-with-resources for the
  unit of work.

## 2.8 ООП — likely questions & answers

- **"Show inheritance + polymorphism."** `User(ABC)` → `Client`/`Hiver`; `calculate_commission()` is
  7% flat for clients vs level-based for hivers (§2.2).
- **"Where's encapsulation?"** Value objects validate in `__post_init__`; `_password_hash` hidden
  behind a property; level-up logic private in `Hiver` (§2.2–2.3).
- **"Name your design patterns."** Repository, Adapter, Strategy, Factory, Builder, Observer, Value
  Object, State machine — each with a file (§2.5).
- **"How is this SOLID?"** One example per letter (§2.4); the headline is Dependency Inversion — the
  domain defines `IPaymentPort`, infrastructure implements it, the factory picks the adapter.
- **"Swap Stripe for PayPal — what changes?"** Write a `PayPalAdapter(IPaymentPort)` and one line in
  `payment_factory`. No use case changes. That's Open/Closed + Adapter in one answer.
- **"Why abstract `User`?"** It can't be instantiated — an account is always a concrete `Client` or
  `Hiver`; the ABC guarantees both implement `get_role`/`calculate_commission`.

---

## One-line file map (open these live during the defence)

- **Geo function / triggers:** `…/migrations/versions/014_create_plpgsql_functions.py`
- **Window-function view:** `…/migrations/versions/015_create_views.py`
- **RLS:** `…/migrations/versions/017_enable_rls_and_secure_view.py`
- **Entities (inheritance/polymorphism):** `domain/entities/user.py`, `…/task.py`
- **Value objects:** `domain/value_objects/{money,rating,work_radius,location}.py`
- **Interfaces (ports):** `domain/interfaces/ports.py`, `…/repositories.py`
- **Patterns:** `domain/services/event_bus.py` (Observer), `…/task_factory.py` (Builder/Factory),
  `infrastructure/payments/payment_factory.py` (Factory/Strategy)
- **Exceptions:** `domain/errors/domain_errors.py`
