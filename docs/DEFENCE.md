# Hiver — Project & Defence Guide

One document to revise from before the defence. It explains **what the site is**, **how it's
built**, **why each technology was chosen**, and gives **per-subject talking points + likely
questions** for РС, ООП, БД and ВОТ. Pair it with [`README.md`](../README.md) (quick start +
endpoints) and [`PROGRESS.md`](../PROGRESS.md) (long-form rationale).

---

## 1. What Hiver is

A two-sided **task marketplace** (think TaskRabbit / rabotim.com) for a city like Sofia.

- A **client** posts a real-world task (cleaning, tutoring, tech help, moving, care, events).
- A **hiver** browses tasks on a map, makes an **offer** (bid), and does the job.
- Money is held in **escrow** until the client confirms completion, then released to the hiver.
- Both sides **review** each other (double-blind), **chat** on the task, and can open a **dispute**.

**Unified accounts:** there is no "pick a role" — every account is *both* a client and a hiver.
One `users` row owns a `clients` row **and** a `hivers` row. So the same person can post a task in
the morning and earn money on someone else's task in the afternoon.

**6 service verticals:** `home, learn, tech, care, move, events`. Some verticals ask "smart"
questions (e.g. `home → property_type`).

---

## 2. Run it / demo script

```bash
cp .env.example .env                       # JWT secret etc.
docker compose up -d postgres redis        # + prometheus grafana for the observability demo
cd backend && uv sync --dev && alembic upgrade head && python -m src.infrastructure.database.seed
uvicorn src.main:app --reload              # http://localhost:8000/docs
# new terminal:
cd frontend && npm install && npm run dev  # http://localhost:5173
```

**Demo flow to show in the defence (5 min):**
1. Register → land on the home/map. Show the account is both client & hiver (Profile page).
2. Post a task with a real address (Google Places autocomplete → pin on the map).
3. Browse tasks on the map / filter by radius, budget, free-text, category.
4. From a second account, make an offer → first account accepts → **escrow holds funds**.
5. Chat opens between the two; show the **Inbox** (`/inbox`) with unread badge.
6. Mark complete → **release escrow** → leave reviews (reveal once both submitted).
7. Show extras: **favorites** (heart), **boost a task** (pinned atop search), **settings** (avatar/bio/skills).
8. ВОТ bonus: `http://localhost:8000/metrics` (Prometheus), Grafana at `:3001`, `/docs` (OpenAPI).

---

## 3. Architecture at a glance

**Clean Architecture** — dependencies point *inward only*:

```
HTTP routers ─► Application (use cases) ─► Domain (entities, value objects)
                                              ▲
                  Infrastructure ─────────────┘  (implements Domain interfaces)
```

- **Domain** (`backend/src/domain/`) — pure Python. No FastAPI, no SQLAlchemy, no Stripe. Entities
  (`Task`, `Client`, `Hiver`, `Offer`, …), value objects (`Money`, `Rating`, `Location`,
  `WorkRadius`), and **interfaces** (`I*Repository`, ports) it *defines* but does not implement.
- **Application** (`backend/src/application/`) — one **use case** per action (e.g.
  `CreateTaskUseCase`, `BoostTaskUseCase`). Depends only on Domain interfaces + DTOs. Never imports
  a concrete repository.
- **Infrastructure** (`backend/src/infrastructure/`) — the outer ring: SQLAlchemy models +
  repositories that *implement* the Domain interfaces, FastAPI routers, payment/storage adapters.
- **Dependency rule enforcement:** the inward arrow means you can swap Postgres for anything, or
  the mock payment adapter for real Stripe, without touching domain or use-case code.

**Request lifecycle (POST /tasks):** router → `get_current_client` dependency (decodes JWT, loads
the Client) → `CreateTaskUseCase.execute(dto)` → `TaskFactory` builds a valid `Task` entity →
`PostgresTaskRepository.save()` persists it (incl. PostGIS point) → DTO response. Errors raised in
the domain become structured JSON in `error_handler.py`.

---

## 4. Tech stack & **why**

| Layer | Choice | Why this one (and what it replaces) |
|---|---|---|
| Language | **Python 3.12/3.13** | Team familiarity; async story is now first-class. |
| Web framework | **FastAPI** | Async, automatic OpenAPI docs, Pydantic validation built in. Replaces Flask/Django — less boilerplate, typed. |
| Validation | **Pydantic v2** | Request/response DTOs validate at the edge; `field_validator`/`model_validator` enforce rules (budget min≤max, coord pairs) before the use case runs. |
| ORM | **SQLAlchemy 2.0 async** + **asyncpg** | Mature, typed, async; asyncpg is the fastest Postgres driver. |
| Migrations | **Alembic** (22 chained) | Versioned, reversible schema history — required for the БД grade. |
| Database | **PostgreSQL 16 + PostGIS** | Relational integrity + geospatial (`ST_DWithin`) for "tasks/hivers near me". |
| Cache / limits | **Redis 7** | Rate-limit counters + session-ish needs. |
| Auth | **JWT (python-jose)** + **pwdlib** (Argon2, bcrypt fallback) | Stateless, scalable tokens; Argon2 is the modern password hash (pwdlib replaced passlib, which failed to import). Social login via **Authlib** (Google/Facebook). |
| Payments | **Adapter** — `MockPaymentAdapter` default, `StripeAdapter` swappable | Demo works with zero Stripe account; one factory swaps to real Stripe. |
| Storage | **Supabase Storage** + **Pillow** | Real object storage for task photos + avatars; Pillow rejects corrupt/truncated uploads. |
| Maps | **Google Maps + Places** (`@vis.gl/react-google-maps`) | Real address autocomplete + pins; **keyless OpenStreetMap fallback** so it runs with no key. |
| Frontend | **React 19 + TypeScript 5 + Vite 8 + Framer Motion** | Typed SPA, fast HMR, animation. |
| Container | **Docker** multi-stage (alpine, non-root, <150 MB) | Small, secure production image. |
| Orchestration | **Kubernetes + Helm** | 2–10 replicas, rolling updates, CPU autoscaling. |
| Observability | **Prometheus + Grafana** | `/metrics` scraped every 15 s; Grafana datasource auto-provisioned. |
| CI/CD | **GitHub Actions** | CI on PRs (lint/type/test/security/docker); CD on push-to-main (build+Helm). |
| IaC | **Terraform** (skeleton) | Declarative cloud provisioning (modules: database, networking). |
| Pkg mgrs | **uv** (Python), **npm** (frontend) | uv is fast + lockfile-driven. |

---

## 5. Feature tour — "what to know about the site"

| Area | What it does | Where it lives |
|---|---|---|
| Auth | Register/login (JWT + refresh), Google/Facebook OAuth, rate-limited | `routers/auth.py`, `use_cases/auth/`, `shared/security.py`, `shared/password.py` |
| Unified accounts | Each account is client **and** hiver; `/users/me` returns both facets | `entities/user.py`, `routers/users.py`, migration 019 (backfill) |
| Tasks | CRUD, 6 verticals, per-vertical "smart" questions, photos, urgent flag | `entities/task.py`, `services/task_factory.py`, `routers/tasks.py` |
| Geo search | Tasks/hivers on a map; filter radius/budget/free-text/category/sort | `repositories/task_repository.py` (`ST_DWithin`), `pages/Tasks.tsx`, `NearbyHivers.tsx` |
| Offers | Hiver bids; client accepts (can't offer on own task) | `routers/offers.py`, `use_cases/offers/` |
| Escrow | Hold on accept, release on complete, refund on cancel | `payments/`, `use_cases/payments/`, `routers/payments.py` |
| Reviews | Double-blind: revealed only when both sides submit (DB trigger) | migration 014 trigger, `routers/tasks.py` reviews |
| Chat + Inbox | Per-task chat (REST polling) + conversations list with unread | `routers/messages.py`, `use_cases/messages/`, `pages/Inbox.tsx` |
| Disputes | Either party opens; locks escrow; resolve by concession | `routers/disputes.py`, `entities/dispute.py` |
| Notifications | In-app feed via Observer/EventBus; SPA polls unread | `services/event_bus.py`, `notifications/in_app_adapter.py` |
| Boosts | Hiver visibility boost + task "feature" (pinned atop search) | `use_cases/boosts/`, `use_cases/tasks/boost_task_use_case.py` |
| Favorites | Save tasks/hivers (heart); `/saved` page | `entities/favorite.py`, `routers/favorites.py`, `context/FavoritesContext.tsx` |
| Profiles/Settings | Edit name/bio/skills/avatar/service location + radius | `use_cases/users/update_profile_use_case.py`, `pages/Settings.tsx` |

---

## 6. Defence by subject

### РС — Software Development (clean code, REST API, architecture)
- **Clean Architecture** with a strict dependency rule (Section 3). Point to the layer folders.
- **RESTful API**: resource-oriented paths, correct verbs (`POST/GET/PATCH/DELETE`), status codes
  (201 create, 204 delete, 422 validation, 401/403 auth). Auto-documented at `/docs` (OpenAPI).
- **Error handling** (`http/middleware/error_handler.py`): domain `AppError` → `{error, message}`
  with the right status; `ValidationError` → 422 with field detail; a `ValueError` safety-net →
  422; unhandled → generic 500 that **never leaks a stack trace**. Structured logging via structlog.
- **Cross-cutting**: JWT auth + refresh, **rate limiting** (slowapi: 5/min register, 10/min login),
  pagination (`PaginatedResult`), DTO validation at the edge.
- **Quality gates**: `ruff`, `mypy --strict`, 294 tests, pre-commit hooks.

### ООП — OOP (SOLID, inheritance, polymorphism, design patterns)
- **Inheritance + polymorphism**: `User` (abstract) → `Client` / `Hiver`. `calculate_commission()`
  differs per subclass and per hiver level (`entities/user.py`) — textbook polymorphism + Liskov.
- **Encapsulation**: `Task` state transitions go through methods (`accept/start/complete/cancel`),
  never by external assignment; invalid transitions raise domain errors (`entities/task.py`).
- **Value Objects** (immutable, self-validating): `Money`, `Rating`, `WorkRadius`, `Location`
  (Haversine distance lives *inside* `Location`).
- **Design patterns** (name the file):
  - **Repository** — `domain/interfaces/repositories.py` + `infrastructure/.../repositories/`.
  - **Adapter / Strategy** — `payments/payment_factory.py` picks `MockPaymentAdapter` vs
    `StripeAdapter`; `storage/storage_factory.py` similarly.
  - **Factory** — `services/task_factory.py` builds the right task per vertical.
  - **Observer** — `services/event_bus.py`: use cases publish events; the in-app notification
    adapter subscribes and persists — neither knows the other.
  - **Interface Segregation** — `IReadableTaskRepository` vs `IWritableTaskRepository`.
  - **DTO** — Pydantic request/response models in `application/dtos/`.
  - **Dependency Injection** — FastAPI `Depends` + `shared/container.py` factories.

### БД — Databases (migrations, procedures, triggers, views, PostGIS, RLS)
- **22 Alembic migrations**, reversible, numbered `001`→`022`.
- **PL/pgSQL triggers** (migration 014): `updated_at` auto-touch on every table; **double-blind
  review reveal** (`trg_reveal_reviews` flips both reviews visible only when the 2nd is submitted);
  `trg_update_hiver_rating` (recomputes rating, +XP, level-up on review reveal).
- **Stored function** `find_hivers_in_radius(lat,lng,radius,vertical)` — PostGIS radius search.
- **View with window functions** `hiver_earnings_monthly` (migration 015): `RANK() OVER`, running
  total, 3-month rolling average; hardened to `security_invoker` in 017.
- **PostGIS**: `Geography(POINT, 4326)` columns, `ST_DWithin`/`ST_Distance` for search,
  `ST_X/ST_Y` to read coords back, GIST indexes (013).
- **Constraints & indexes**: budget-range `CHECK` (018), unique constraints (offers, reviews,
  favorites 021), partial indexes (`WHERE status='open'`), composite indexes.
- **Row Level Security** (017): default-deny on every public table so Supabase's auto PostgREST API
  can't bypass the backend; the app connects as the owner role (BYPASSRLS). Favorites table also
  RLS-locked (021).
- **Migration hygiene** worth mentioning: PostGIS columns need raw `op.execute()` (GeoAlchemy2
  fails inside `create_table`); partial-index predicates must stay `IMMUTABLE` (no `NOW()`).

### ВОТ — Virtualization & Cloud (Docker, K8s, CI/CD, monitoring)
- **Docker**: multi-stage `backend/Dockerfile` — `deps` stage builds the venv, `production` stage is
  alpine + runtime libs only, **non-root user**, healthcheck, stripped `.so` files; CI enforces a
  **<150 MB** image.
- **docker-compose**: backend + Postgres(PostGIS) + Redis + Prometheus + Grafana, with healthchecks
  and named volumes.
- **Kubernetes Helm chart** (`infra/k8s/charts/hiver/`): `Deployment` (rolling update, liveness/
  readiness on `/health`, secrets via `envFrom`), `Service`, **HPA** (2–10 replicas at 70% CPU),
  `Ingress`. Validate: `helm lint` / `helm template`.
- **CI/CD** (GitHub Actions): **CI** on PRs — ruff, `mypy --strict`, `pytest --cov-fail-under=80`
  (with Postgres+Redis service containers), `pip-audit`, trufflehog secret scan, Docker build.
  **CD** on push-to-main — build/push image, `helm upgrade --install`.
- **Observability**: backend `/metrics` (prometheus-fastapi-instrumentator) scraped by Prometheus;
  Grafana auto-provisions the Prometheus datasource; alert rules in `infra/prometheus/alerts.yml`.
- **IaC**: Terraform skeleton (`infra/terraform/`, modules: database, networking).
- **Supply chain**: Dependabot (pip/npm/actions/docker), CODEOWNERS, pre-commit.

---

## 7. Likely questions → crisp answers

- **"Why Clean Architecture for a school project?"** It makes the domain testable without a DB (294
  fast tests), and lets us swap infrastructure (mock→real Stripe, Postgres→anything) without
  touching business rules. The dependency rule is the whole point.
- **"How do you stop someone offering on their own task / completing someone else's?"** Domain
  guards: `CannotOfferOnOwnTaskError`, and `Task.complete()` checks `actor == client_id`. Auth
  dependencies load the acting user from the JWT.
- **"How is the password stored?"** Argon2 via pwdlib; never plaintext; OAuth-only accounts have a
  null hash and can't password-login.
- **"What makes reviews fair?"** Double-blind: a DB trigger reveals both reviews only after both are
  submitted, so neither side can retaliate.
- **"How does 'near me' work?"** PostGIS `Geography` points + `ST_DWithin` in a stored function;
  GIST-indexed. Coordinates come from Google Places (real addresses).
- **"Is the payment real?"** Architecturally yes (escrow hold/release/refund through a payment
  *port*); the default adapter is a mock so the demo needs no Stripe account — flip one factory to
  go live.
- **"Does CI actually run?"** Yes, on every PR to `main`/`develop` (lint + types + tests≥80% +
  security + docker build). CD is written but deploying for real needs a cluster + secrets (below).

---

## 8. Honest gaps (so nothing surprises you)

- **CD doesn't deploy yet** — the workflow + Helm chart are complete, but actually shipping needs a
  Kubernetes cluster, registry secrets (`REGISTRY_USER`/`REGISTRY_PASSWORD`), a cluster-auth step in
  `cd.yml`, and a `hiver-secrets` Secret. CI (the graded part) runs on PRs.
- **Grafana** ships a provisioned dashboard *"Hiver — Backend Overview"* (datasource + dashboard
  auto-loaded on startup: up, request rate, error rate %, p50/p95/p99 latency, status-class
  breakdown, top endpoints). Prometheus + `/metrics` + alerts are real.
- **Stripe & push (FCM)** are scaffolded behind ports; the working defaults are the mock payment
  adapter and in-app notifications.
- **Terraform** is an unapplied skeleton.
- **Chat** uses WebSockets for live updates, with REST polling (10 s) as a reconnect fallback.
- **Prometheus scrape vs host-run backend** — Prometheus targets the compose `backend` service, so
  to see metrics flowing run the backend *in compose* (`docker compose up backend`), not only the
  host dev server.
