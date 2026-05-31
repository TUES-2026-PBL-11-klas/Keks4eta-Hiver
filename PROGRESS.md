# Hiver — Project Progress & Stack Reference

## What Is Hiver?

Hiver is a **two-sided task marketplace** built as a school project. Clients post tasks (cleaning, tutoring, tech help, moving, etc.) and Hivers (service providers) bid on them. The client picks an offer, pays into escrow, the hiver completes the task, and the client releases the funds.

**Graded across 4 subjects:**
| Subject | Focus | Grade requirement |
|---------|-------|-------------------|
| РС (Software Development) | Clean code, architecture, REST API | 6/6 |
| ООП (OOP) | Inheritance, polymorphism, SOLID, design patterns | 6/6 |
| БД (Databases) | Schema design, migrations, stored procedures, views | 6/6 |
| ВОТ (Virtualization & Cloud) | Docker, Kubernetes, CI/CD, monitoring | 6/6 |

**Architecture:** Clean Architecture — the code is split into 4 strict layers that can only depend inward:

```
HTTP (routers, middleware)        ← outermost, talks to the internet
  ↓
Application (use cases, DTOs)     ← orchestrates business flows
  ↓
Domain (entities, value objects)  ← pure business logic, no DB or HTTP
  ↑
Infrastructure (DB, Stripe, etc.) ← concrete implementations of domain interfaces
```

---

## Current Status at a Glance

| Phase | Name | Status | Commit |
|-------|------|--------|--------|
| 1 | Project Scaffold | ✅ Done | `bfab23f` |
| 2 | Domain Layer (OOP) | ✅ Done | `05b3bd1` |
| 3 | Database Migrations | ✅ Done | `c12b244` |
| 4 | API Layer | ✅ Done | `b0b0447` |
| 5 | Tests + CI/CD + Observability | ⏳ In progress — domain unit tests done (97, all green); CI/templates/CODEOWNERS/dependabot in place; use-case + integration tests next | — |
| 6 | Responsive Frontend + Social Login | ✅ Done — responsive web app, all endpoints wired, Google/Facebook OAuth | — |

---

## Tech Stack

### Backend

| Technology | Version | Why we chose it | What it does |
|-----------|---------|-----------------|--------------|
| **Python** | 3.12 | Latest stable, best async support, type hints | Language |
| **FastAPI** | ≥0.111 | Auto-generates Swagger/OpenAPI docs, async-native, uses Pydantic v2 | HTTP API framework |
| **Uvicorn** | ≥0.30 | ASGI server — runs async code in production | Serves the FastAPI app |
| **Pydantic v2** | ≥2.7 | Validates request bodies and serializes responses, catches bad input at the boundary | Request/response schemas (DTOs) |
| **pydantic-settings** | ≥2.3 | Loads `.env` file into a typed `Settings` object — no raw `os.getenv()` | Config management |
| **SQLAlchemy 2.0** | ≥2.0.30 | Modern async ORM, type-safe queries, works with alembic | Database ORM |
| **asyncpg** | ≥0.29 | Fastest async PostgreSQL driver available | Low-level DB connection |
| **Alembic** | ≥1.13 | Tracks and applies schema changes as versioned migrations — required for БД grade | Database migrations |
| **PostgreSQL 16 + PostGIS** | external | Full relational DB + `ST_DWithin` geospatial queries for finding nearby hivers | Primary database |
| **GeoAlchemy2** | ≥0.15 | Maps PostGIS `Geography(POINT)` columns to SQLAlchemy ORM models | Geo ORM columns |
| **Redis 7** | external | Fast in-memory store for sessions and rate limiting | Cache layer |
| **python-jose** | ≥3.3 | Encodes and decodes JWT tokens | Auth token generation |
| **passlib[bcrypt]** | ≥1.7 | Hashes passwords with bcrypt — never stores plain text | Password security |
| **Authlib** | ≥1.3 | OAuth 2.0 / OIDC client for Google + Facebook social login (infrastructure only) | Social login |
| **itsdangerous** | ≥2.2 | Signs the short-lived session cookie that carries OAuth state across the provider round-trip | OAuth state signing |
| **Stripe** | ≥9.0 | Payment intents with manual capture for escrow hold/release | Payments |
| **httpx** | ≥0.27 | Async HTTP client for calling external APIs (Google Maps, Supabase) | External API calls |
| **structlog** | ≥24.0 | Structured JSON logging instead of plain print() | Observability |
| **prometheus-fastapi-instrumentator** | ≥7.0 | Auto-instruments every FastAPI endpoint with Prometheus metrics | Monitoring |
| **dependency-injector** | ≥4.41 | DI container library (currently using manual factory pattern instead) | Dependency wiring |
| **uv** | latest | Replaces pip — installs packages 10-100x faster | Package manager |

#### Why PostgreSQL and NOT Supabase as the main DB?

Supabase is used only for **Storage** (task images) and **Realtime** (push notifications). The main database is self-hosted PostgreSQL because:
- PostGIS is needed for geospatial queries (`find_hivers_in_radius` stored function)
- We need full SQL control for PL/pgSQL triggers, stored procedures, and window-function views
- Alembic migrations are required for the Databases subject grade — Supabase doesn't support Alembic

---

### Frontend

| Technology | Version | Why | What it does |
|-----------|---------|-----|--------------|
| **React 18** | 18.3.1 | Hooks, concurrent mode, massive ecosystem | UI framework |
| **React Router 6** | 6.23.1 | Client-side routing, no page reloads | Navigation between pages |
| **TypeScript 5** | 5.4.5 | Type safety — catches API contract mismatches at compile time | Language layer |
| **Vite 5** | 5.3.1 | Much faster than Webpack, native ES modules, instant HMR | Build tool & dev server |
| **CSS Modules** | built-in | Scoped styles per component, no global class name collisions | Component styling |
| **Framer Motion** | ≥11.3 | Declarative animation — scroll-reveals, page transitions, modal enter/exit | Motion / animation |

**Design system — "The Hive":** warm editorial-utilitarian direction built on the existing brand.
- **Palette:** Honey (`#EE7F22`) + deep navy ink (`#00224F`) on a warm paper field (`#FBEFE0`); tints and tones are exposed as CSS custom properties in `src/index.css` (`--honey*`, `--ink*`, `--paper`, `--card`, `--line`, semantic state colors).
- **Type:** tri-font system — **Fraunces** (optical serif) for display/brand, **Hanken Grotesk** for body, **Space Mono** kept deliberately for prices/tags/meta (a callback to the original identity). Loaded via Google Fonts in `index.html`.
- **Responsive scale:** fluid type (`clamp()`), spacing scale, container-width and breakpoint tokens in `index.css` drive a single layout across phone → tablet → desktop.
- **Motif:** honeycomb — hexagon brand mark, hex category glyphs, hex avatars, a faint honeycomb texture wash, and a raised hex "Post" action in the mobile tab bar.
- **Layout:** one **responsive `AppShell`** wraps every route — a fixed left sidebar + top bar on desktop (≥1024px), inline top nav on tablet, and a bottom tab bar on phone (<640px). Chrome is hidden on auth routes. Replaces the old fixed 440px phone-frame device.
- **Components:** reusable UI primitives in `components/ui/` (`Button`, `Card`, `Badge`, `Avatar`, `Skeleton`, `Spinner`, `EmptyState`, `Stars`), `Modal`, `TaskCard`, `Reveal` (scroll-into-view), `Input`, `ProtectedRoute`, and a stroke-based SVG `icons` set. Motion: scroll reveals + route transitions via Framer Motion, all honoring `prefers-reduced-motion`.
- **State:** `AuthContext` (`useAuth`) holds the session, hydrates from `GET /users/me`, and transparently refreshes expired access tokens; a typed `lib/services.ts` wraps every backend endpoint.

---

### Infrastructure & DevOps

| Tool | Why | What it does |
|------|-----|--------------|
| **Docker** | Reproducible environment — runs identically on any machine | Containerizes backend, frontend, and all services |
| **docker-compose** | Starts all 5 services with one command | Orchestrates backend + postgres + redis + prometheus + grafana |
| **Prometheus** | Industry-standard pull-based metrics | Scrapes `/metrics` from backend every 15 seconds |
| **Grafana** | Visual dashboards on top of Prometheus | Displays latency, error rate, business KPIs |
| **Kubernetes + Helm** | Production-grade orchestration | Runs 2–10 replicas with auto-scaling (70% CPU trigger) |
| **Terraform** | Infrastructure-as-Code | Provisions AWS/GCP resources declaratively |

**Docker services and ports:**
| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| backend | custom build | 8000 | FastAPI app |
| postgres | postgis/postgis:16-3.4-alpine | 5432 | Primary DB |
| redis | redis:7-alpine | 6379 | Cache |
| prometheus | prom/prometheus | 9090 | Metrics scraper |
| grafana | grafana/grafana | 3001 | Dashboards |

---

## Phase Breakdown

### Phase 1 — Project Scaffold ✅
**Commit:** `bfab23f`

**What it is:** Creating the skeleton of the project — folder structure, config files, Docker setup — before writing any business logic. This forces you to make architectural decisions upfront.

**What was built:**
- Clean Architecture folder layout: `backend/src/{domain,application,infrastructure,shared}/`
- `pyproject.toml` with all 18+ dependencies pinned
- Multi-stage `Dockerfile` — stage 1 installs deps, stage 2 copies only what's needed (keeps image small, non-root user `hiver`, healthcheck included)
- `docker-compose.yml` with 5 services (backend, postgres, redis, prometheus, grafana)
- `.env` file with dev credentials
- `.gitignore`, `.pre-commit-config.yaml`
- Vite + React + TypeScript frontend scaffold
- Frontend pages: Home, Login, Register, Tasks, Profile

**Why this phase first:** Every file written in later phases needs a home. Getting the structure right before writing code prevents costly reorganization later.

---

### Phase 2 — Domain Layer (OOP) ✅
**Commit:** `05b3bd1`

**What it is:** The business logic core. This layer has **zero** knowledge of databases or HTTP — it's pure Python classes that model how the business works. This is where all the OOP patterns live.

**What was built:**

**Entities (Aggregate Roots):**
- `user.py` — Abstract `User` ABC → `Client` + `Hiver` subclasses
  - Polymorphism: `get_role()`, `calculate_commission()` override per subclass
  - Encapsulation: password hashing internal, level-up logic hidden
  - Hiver levels: beginner → experienced → master → legend (based on XP)
- `task.py` — Task with status state machine: `OPEN → ACCEPTED → IN_PROGRESS → COMPLETED`
- `offer.py` — Offer (hiver bid) with gated transitions: `PENDING → ACCEPTED/REJECTED`
- `transaction.py` — Escrow: `HELD → RELEASED/REFUNDED/DISPUTED`, factory method `create_for_task()`
- `review.py` — Blind-reveal: both parties submit independently, neither can read until both have submitted

**Value Objects (Immutable):**
- `money.py` — `Money(Decimal)` with safe arithmetic, never leaks raw floats
- `location.py` — `Location(lat, lng)` with Haversine distance calculation
- `rating.py` — `Rating(0.0–5.0)` with rolling average recalculation
- `work_radius.py` — `WorkRadius` constrained to `{1, 2, 5, 10, 15, 20}` km tiers only

**Domain Errors (16 typed exceptions):**
```
AppError (base)
├── NotFoundError (404) → Task/Hiver/Client/Offer/TransactionNotFoundError
├── BusinessRuleViolationError (422) → EscrowAlreadyReleased, InsufficientRating, TaskAlreadyAccepted, OfferAlreadyExists...
├── UnauthorizedActionError (403)
└── Auth errors (401) → InvalidCredentials, TokenExpired, InvalidToken
```

**Repository Interfaces (SOLID-D):**
- `IRepository[T, ID]` — generic base with TypeVar/Generic
- `ITaskRepository`, `IClientRepository`, `IHiverRepository`, `IOfferRepository`, `ITransactionRepository`, `IReviewRepository`
- Split into `IReadableTaskRepository` + `IWritableTaskRepository` (Interface Segregation Principle)

**Domain Services:**
- `task_factory.py` — Factory + Builder pattern: dispatches to vertical-specific builder (`HomeTaskBuilder`, `LearnTaskBuilder`, etc.)
- `event_bus.py` — Observer pattern: `subscribe(event_type, handler)` + `publish(event)`
- `search_sort.py` — Strategy pattern: pluggable sort algorithms

**Infrastructure Stubs:**
- `stripe_adapter.py` — Adapter pattern wrapping Stripe SDK
- `database/transaction.py` — Context Manager for DB transaction scope
- `concurrency/semaphore.py` — Rate-limiting semaphore utility

**OOP patterns explicitly used (for ООП grade):**
All 5 SOLID principles, Abstraction, Encapsulation, Inheritance, Polymorphism, Generics (TypeVar), Factory, Builder, Observer, Strategy, Repository, Adapter, Context Manager, Value Object, State Machine

---

### Phase 3 — Database Migrations ✅
**Commit:** `c12b244`

**What it is:** SQLAlchemy ORM models mapping to database tables, plus 16 Alembic migrations that build the full schema from scratch in order.

**SQLAlchemy Models (13 tables):**
`users`, `clients`, `hivers`, `skills`, `hiver_skills` (join), `tasks`, `offers`, `transactions`, `reviews`, `messages`, `disputes`, `boosts`, `notification_log`

**The 16 Migrations:**
| # | Migration | Creates |
|---|-----------|---------|
| 001 | create_extensions | uuid-ossp, pgcrypto, PostGIS |
| 002 | create_users_table | `users` base table |
| 003 | create_clients_hivers | `clients` + `hivers` (1-to-1 with users, PostGIS `Geography(POINT)` on hivers) |
| 004 | create_skills | `skills` + `hiver_skills` join table |
| 005 | create_tasks | `tasks` with `JSONB smart_answers`, `ARRAY image_urls`, `Geography location_point` |
| 006 | create_offers | `offers` with unique constraint (task_id, hiver_id) |
| 007 | create_transactions | `transactions` escrow table with Stripe payment intent |
| 008 | create_reviews | `reviews` with unique (task_id, reviewer_id) |
| 009 | create_messages | `messages` chat table |
| 010 | create_disputes | `disputes` conflict resolution |
| 011 | create_boosts | `boosts` premium visibility feature |
| 012 | create_notification_log | audit trail for notifications |
| 013 | create_all_indexes | Performance indexes: partial (WHERE status='open'), composite, GIST |
| 014 | create_plpgsql_functions | 3 triggers + 1 stored function (see below) |
| 015 | create_views | `hiver_earnings_monthly` view with window functions |
| 016 | add_oauth_to_users | `password_hash` made nullable; `oauth_provider` + `oauth_id` columns; partial unique index on (provider, id) for social login |

**PL/pgSQL Triggers (migration 014):**
- `trg_*_updated_at` — Auto-updates `updated_at` timestamp on all tables
- `trg_reveal_reviews` — When 2nd review is submitted, flips both `is_revealed = true`
- `trg_update_hiver_rating` — When review reveals: recalculates `avg_rating`, increments `completed_tasks`, adds 10 XP, recalculates level (100 XP → experienced, 500 → master, 1500 → legend)

**Stored Function (migration 014):**
```sql
find_hivers_in_radius(lat, lng, radius_km, vertical)
-- PostGIS ST_DWithin for geographic radius query
-- Optional vertical filter via skill lookup
-- Only returns hivers where is_available_now = true
-- Orders by distance ascending
```

**Database View (migration 015):**
```sql
hiver_earnings_monthly
-- RANK() within month by earnings
-- Running total (cumulative earnings per hiver)
-- 3-month rolling average (trend)
-- Only released transactions
```

**Why raw SQL for PostGIS columns:** GeoAlchemy2's `Geography` type cannot be used inside Alembic's `op.create_table()` DDL helper — it only works with `op.execute()` raw SQL strings.

**Seed data for development:**
- Clients: alice@example.com, bob@example.com
- Hivers: maria (master/4.9★), stefan (experienced/4.7★), ivan (beginner/4.5★)
- 8 skills, 3 open tasks

---

### Phase 4 — API Layer ✅ (committed `b0b0447`)

**What it is:** Everything that connects the domain layer to the outside world — FastAPI routers, request/response DTOs, use cases that orchestrate business flows, and concrete repository implementations that talk to Postgres.

**What's been built:**

**Security & Session:**
- `shared/security.py` — `create_access_token()`, `create_refresh_token()`, `decode_token()` (raises `TokenExpiredError` / `InvalidTokenError`)
- `infrastructure/database/session.py` — async engine + `AsyncSessionLocal` session factory

**DTOs (Pydantic v2 request/response schemas):**
- `auth_dtos.py` — `RegisterRequest`, `LoginRequest`, `TokenResponse`
- `task_dtos.py` — `CreateTaskRequest`, `TaskSummaryResponse`, `TaskDetailResponse`
- `offer_dtos.py` — `CreateOfferRequest`, `OfferResponse`
- `user_dtos.py` — `ClientProfileResponse`, `HiverProfileResponse`, `UpdateHiverAvailabilityRequest`, `HiverSearchResult`
- `review_dtos.py` — `SubmitReviewRequest`, `ReviewResponse`

**Repositories (domain ↔ database translation):**
- `user_repository.py` — `PostgresClientRepository` + `PostgresHiverRepository` (PostGIS `find_available_near`)
- `task_repository.py` — `PostgresTaskRepository` (raw SQL for PostGIS `find_nearby` + SQLAlchemy `search`)
- `offer_repository.py` — `PostgresOfferRepository`
- `transaction_repository.py` — `PostgresTransactionRepository`
- `review_repository.py` — `PostgresReviewRepository` (blind-reveal enforced by DB trigger)

**Use Cases (one class = one business operation):**
| Use Case | What it does |
|----------|-------------|
| `RegisterUseCase` | Checks duplicate email, hashes password, creates Client or Hiver, returns tokens |
| `LoginUseCase` | Finds user by email (tries client then hiver), verifies bcrypt hash, returns tokens |
| `CreateTaskUseCase` | Checks client rating ≥ 2.0, uses TaskFactory for vertical validation, saves task |
| `GetTaskUseCase` | Finds task by ID, raises TaskNotFoundError if missing |
| `ListClientTasksUseCase` | Returns paginated tasks for a client |
| `SearchTasksUseCase` | Public filterable search (vertical, status, urgency, budget range) |
| `StartTaskUseCase` | Hiver moves task ACCEPTED → IN_PROGRESS (entity enforces actor + state) |
| `CompleteTaskUseCase` | Client moves task IN_PROGRESS → COMPLETED |
| `CancelTaskUseCase` | Client cancels non-completed task |
| `FindHiversNearbyUseCase` | PostGIS geo-search via `find_hivers_in_radius` stored function |
| `CreateOfferUseCase` | Checks task is OPEN, hiver hasn't already bid, creates offer |
| `AcceptOfferUseCase` | Accepts chosen offer, rejects all other pending offers, transitions task to ACCEPTED |
| `ReleaseEscrowUseCase` | Verifies client owns task, releases held funds, marks task COMPLETED |
| `SubmitReviewUseCase` | Submits review for completed task; DB trigger handles blind-reveal pair |
| `ListTaskReviewsUseCase` | Lists reviews for a task (filterable by `is_revealed`) |
| `ListUserReviewsUseCase` | Lists all revealed reviews received by a user |

**HTTP Dependencies:**
- `get_session` — yields `AsyncSession` per request (with transaction)
- `get_current_client` — extracts JWT, checks role == "client", loads Client entity
- `get_current_hiver` — same for hiver role

**Error Handler Middleware:**
- `AppError` → `{"error": "CODE", "message": "..."}` with correct HTTP status
- `ValidationError` → 422 with field-level details
- `Exception` → 500 generic error (never leaks stack traces)

**API Endpoints built:**
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | /health | None | Liveness check |
| POST | /auth/register | None | Sign up as client or hiver — **rate-limited 5/min/IP** (slowapi) |
| POST | /auth/login | None | Get access + refresh tokens — **rate-limited 10/min/IP** |
| POST | /tasks | Client JWT | Post a new task |
| GET | /tasks | Client JWT | List my tasks (paginated) |
| GET | /tasks/search | None | Public search — vertical / status / urgency / budget filters |
| GET | /tasks/{id} | None | Get task details |
| POST | /tasks/{id}/start | Hiver JWT | Move task accepted → in_progress |
| POST | /tasks/{id}/complete | Client JWT | Mark task done |
| POST | /tasks/{id}/cancel | Client JWT | Cancel non-completed task |
| POST | /tasks/{id}/reviews | Auth | Submit review (blind-reveal via DB trigger) |
| GET | /tasks/{id}/reviews | None | List task reviews (`only_revealed=true` by default) |
| POST | /tasks/{id}/offers | Hiver JWT | Submit a bid |
| GET | /tasks/{id}/offers | Client JWT | See all bids on my task |
| POST | /tasks/{id}/offers/{id}/accept | Client JWT | Accept a bid |
| POST | /payments/tasks/{id}/release | Client JWT | Release escrow to hiver |
| GET | /users/{id}/reviews | None | All revealed reviews received by user |
| GET | /users/clients/{id} | None | View client profile |
| GET | /users/hivers/{id} | None | View hiver profile |
| GET | /users/hivers/nearby | None | PostGIS geo-search — `lat, lng, radius_km, vertical?` |
| PATCH | /users/hivers/me/availability | Hiver JWT | Toggle available now |

**Deferred to Phase 5 (non-blocking for grading of Phase 4):**
- Real-time chat / message endpoints (WebSockets via Supabase Realtime — design only)
- Boost-listing endpoints (premium upsell — table + model exist, no flow yet)
- Dispute resolution endpoint (table + model exist, no flow yet)

---

### Phase 5 — Tests, CI/CD, Observability ⏳ Repo infra in place, tests not started

**What it is:** Making the project production-ready and proving it works automatically.

**Already in place:**
- **GitHub Actions CI** — `.github/workflows/ci.yml` (lint + mypy strict + pytest+coverage gate ≥80% + pip-audit + trufflehog + docker build with 150MB size cap)
- **GitHub Actions CD** — `.github/workflows/cd.yml` (docker push + Helm upgrade on `main`)
- **PR template** — enforces doc-sync checklist (`.github/pull_request_template.md`)
- **Issue templates** — bug + feature, with subject/phase tagging (`.github/ISSUE_TEMPLATE/`)
- **CODEOWNERS** — auto-request reviews per path
- **Dependabot** — weekly pip / npm / actions / docker updates
- **CONTRIBUTING.md** — workflow + doc-sync + commit conventions
- **CLAUDE.md** — Clean Architecture rules, DB rules, doc-sync rule for AI-assisted contributions
- **Shared Claude Code tooling** — `.claude/settings.json` (team plugin allow-list) + `.claude/skills/` (11 vendored design/UX skills) so every teammate gets the same AI assistants on `git pull` + restart. Setup + third-party attribution in `.claude/README.md`. Personal overrides stay in the git-ignored `.claude/settings.local.json`.

**Done:**
- **Domain unit tests** — 97 tests, all green (`backend/tests/unit/domain/`): value objects (Money, Rating, WorkRadius, Location invariants + Haversine) and entity state machines (Task/Offer/Transaction lifecycles, Review blind-reveal, User Client/Hiver polymorphism + level-ups). Pure Python, no DB. `conftest.py` puts `src` on `sys.path`. Run with `pytest tests/unit/domain -o addopts=""` (coverage gate disabled until the suite is fuller).

**Still planned:**
- **Use-case tests** — application use cases with in-memory fake repositories
- **Integration tests** — repositories against a real test database, API HTTP tests
- **Coverage target** — 80% minimum (already enforced by `pytest-cov` in CI; suite is empty)
- **Kubernetes deployment** — Helm chart with 2–10 replicas, rolling updates, zero downtime
- **Prometheus dashboards** — latency p50/p99, error rate, requests per second, escrow release lag
- **Alert rules already configured:**
  - HTTP 5xx error rate > 5% → critical
  - DB connection pool > 80% → warning
  - Escrow release job stale > 2 hours → critical

---

### Phase 6 — Responsive Frontend + Social Login ✅

**What it is:** Turning the phone-only mockup into a true responsive web app, wiring every backend
endpoint to a real page, and adding Google/Facebook sign-in.

**Backend:**
- **Social login (Authlib)** — `GET /auth/oauth/{provider}/login` → provider consent →
  `GET /auth/oauth/{provider}/callback` exchanges the code, runs `OAuthLoginUseCase`
  (find-by-provider → link-by-email → create passwordless account), and redirects to the SPA with
  tokens in the URL fragment. Domain `User` gained nullable `password_hash` + `oauth_provider`/
  `oauth_id` (migration 016). Providers are read from env; an unconfigured provider returns a clear
  503 instead of a 500.
- **`POST /auth/refresh`** — rotates an access/refresh pair (role resolved from the repositories).
- **`GET /users/me`** — role-aware current-user endpoint the SPA hydrates from.
- **`/api/v1` prefix** — all feature routers are now mounted under `/api/v1` (matching what the SPA
  always expected); `/health` stays at the root. `SessionMiddleware` added for the OAuth state cookie.

**Frontend:**
- **Responsive `AppShell`** — desktop sidebar + top bar, tablet inline nav, phone bottom-tab bar;
  fluid type + spacing tokens; replaces the fixed 440px device frame.
- **Auth layer** — `AuthContext`/`useAuth`, `/auth/callback` route, `ProtectedRoute` guard,
  transparent refresh-on-401, Google + Facebook buttons on Login/Register.
- **Pages** — Home (responsive hero + reveals), Tasks (filters + grid), TaskDetail (full lifecycle:
  offers submit/accept, start/complete/cancel, escrow release, reviews), PostTask, Dashboard
  (client tasks / hiver stats + availability), NearbyHivers (PostGIS search), Profile (editable
  availability), PublicProfile (hiver/client + reviews).
- **Motion** — Framer Motion scroll reveals + route transitions, `prefers-reduced-motion` aware.

**Verification:** frontend `tsc` typecheck + `eslint` (max-warnings 0) + `vite build` all pass;
backend `OAuthLoginUseCase` unit test added (`tests/unit/application/`, 4 cases green).

---

## Design Patterns Reference

| Pattern | Where | Purpose |
|---------|-------|---------|
| Abstract Base Class | `domain/entities/user.py` | `User` → `Client` / `Hiver` inheritance |
| Polymorphism | `user.py` | `get_role()`, `calculate_commission()` differ per subclass |
| State Machine | `task.py`, `offer.py`, `transaction.py` | Status transitions validated by methods, not raw assignment |
| Factory Method | `transaction.py` | `Transaction.create_for_task()` computes fees in one call |
| Factory + Builder | `domain/services/task_factory.py` | `TaskFactory` dispatches to `HomeTaskBuilder`, `LearnTaskBuilder`, etc. |
| Observer | `domain/services/event_bus.py` | `EventBus.publish()` → subscribed handlers called automatically |
| Strategy | `domain/services/search_sort.py` | Pluggable sort algorithm per query |
| Repository | `domain/interfaces/repositories.py` + `infrastructure/database/repositories/` | Data access abstraction — use cases never touch SQL |
| Adapter | `infrastructure/payments/stripe_adapter.py` | Wraps Stripe SDK behind `IPaymentPort` |
| Context Manager | `infrastructure/database/transaction.py` | `async with db_transaction(session):` for safe DB scoping |
| Value Object | `domain/value_objects/` | Immutable, validated, self-contained logic (Money, Location, Rating, WorkRadius) |
| Dependency Injection | `shared/container.py` + `http/dependencies.py` | Repos and use cases wired together without tight coupling |
| Blind-Reveal | `domain/entities/review.py` | Reviews hidden until both parties submit |
| Escrow | `domain/entities/transaction.py` | Funds held until task confirmed complete |

---

## File Structure Overview

```
Keks4eta-Hiver/
├── backend/
│   ├── Dockerfile                        Multi-stage, non-root, healthcheck
│   ├── pyproject.toml                    All dependencies + dev tools
│   ├── alembic.ini                       Alembic config
│   └── src/
│       ├── main.py                       FastAPI app, routers, lifespan
│       ├── shared/
│       │   ├── config.py                 Pydantic Settings (reads .env)
│       │   ├── security.py               JWT create/decode
│       │   ├── container.py              DI factory functions
│       │   └── concurrency/semaphore.py  Rate limiting
│       ├── domain/
│       │   ├── entities/                 user, task, offer, transaction, review
│       │   ├── value_objects/            money, location, rating, work_radius
│       │   ├── services/                 task_factory, event_bus, search_sort
│       │   ├── interfaces/               repositories.py, ports.py
│       │   └── errors/domain_errors.py   16 typed exceptions
│       ├── application/
│       │   ├── use_cases/                auth/, tasks/, offers/, payments/
│       │   └── dtos/                     auth, task, offer, user DTOs
│       └── infrastructure/
│           ├── database/
│           │   ├── session.py            Async engine + session factory
│           │   ├── models/               13 SQLAlchemy models
│           │   ├── repositories/         4 Postgres repository implementations
│           │   ├── migrations/versions/  001–016 Alembic migrations
│           │   └── seed.py               Dev seed data
│           ├── http/
│           │   ├── dependencies.py       get_session, get_current_client/hiver
│           │   ├── middleware/            error_handler.py
│           │   └── routers/              auth, tasks, offers, users, payments
│           ├── payments/stripe_adapter.py
│           ├── geo/worker.py
│           └── storage/
├── frontend/
│   ├── src/
│   │   ├── pages/                        Home, Login, Register, AuthCallback, Tasks,
│   │   │                                 TaskDetail, PostTask, Dashboard, NearbyHivers,
│   │   │                                 Profile, PublicProfile
│   │   ├── components/                   AppShell, ProtectedRoute, TaskCard, Modal, Reveal,
│   │   │                                 Input, icons, ui/ (Button, Card, Badge, Avatar, …)
│   │   ├── context/AuthContext.tsx       Session state, /users/me hydrate, token refresh
│   │   ├── lib/api.ts                    HTTP client (Bearer + refresh-on-401)
│   │   ├── lib/services.ts               Typed wrappers for every backend endpoint
│   │   └── types/index.ts                Me, Task, Offer, Review, profiles, … interfaces
│   └── Dockerfile                        Node build → Nginx serve
├── infra/
│   ├── prometheus/                       prometheus.yml + alerts.yml
│   ├── grafana/                          Dashboard definitions
│   ├── k8s/charts/hiver/                 Helm chart (2-10 replicas, HPA)
│   └── terraform/                        AWS/GCP provisioning
├── .claude/                              Shared team Claude Code setup
│   ├── settings.json                     Team plugin allow-list (committed)
│   ├── skills/                           11 vendored design/UX skills (committed)
│   └── README.md                         Teammate setup + third-party attribution
├── docker-compose.yml                    5-service local stack
├── .env                                  Dev credentials (not committed)
└── PROGRESS.md                           This file
```
