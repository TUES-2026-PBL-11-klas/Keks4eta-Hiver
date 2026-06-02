# Hiver

A two-sided task marketplace — clients post real-world tasks (cleaning, tutoring, tech help, moving, etc.) and **hivers** bid on them. Built as a school project, graded across 4 subjects.

> **Full reference:** see [`PROGRESS.md`](./PROGRESS.md) for the deep-dive (tech rationales, phase breakdowns, design patterns, gap analysis).
> **For Claude Code contributors:** see [`CLAUDE.md`](./CLAUDE.md) for repo conventions (Clean Architecture rules, doc-sync rule).

## Phase Status

| Phase | Description | Status | Commit |
|---|---|---|---|
| 1 | Project scaffold | ✅ Done | `bfab23f` |
| 2 | Domain layer (OOP) | ✅ Done | `05b3bd1` |
| 3 | Database migrations + seed | ✅ Done | `c12b244` |
| 4 | API layer (FastAPI routers + DI) | ✅ Done | `b0b0447` |
| 5 | Tests + CI/CD + observability | ⏳ Domain unit tests done (97, green); use-case + integration tests next | — |
| 6 | Responsive frontend + social login | ✅ Done — full responsive web app, all endpoints wired, Google/Facebook OAuth | — |
| 7 | Marketplace completion | 🔄 In progress — escrow end-to-end ✅, in-app notifications (Observer/EventBus) ✅, shared Supabase DB + RLS ✅; remaining: full test coverage & polish | — |

## Tech Stack (short)

| Layer | Choice |
|---|---|
| Language | Python 3.12 |
| Backend | FastAPI + Pydantic v2 + Uvicorn |
| ORM | SQLAlchemy 2.0 (async) + asyncpg |
| Migrations | Alembic (17 chained) |
| Database | PostgreSQL 16 + PostGIS |
| Cache | Redis 7 |
| Auth | JWT (python-jose) + passlib[bcrypt]; social login via Authlib (Google + Facebook) |
| Payments | Stripe (manual capture for escrow) |
| Storage | Supabase Storage (task images) |
| Frontend | React 18 + TypeScript 5 + Vite 5 + Framer Motion (responsive web app) |
| Container | Docker (multi-stage) + docker-compose |
| Infra (target) | Kubernetes + Helm + Terraform |
| Observability | Prometheus + Grafana |
| Package mgr | `uv` (Python), `npm` (frontend) |

Rationales for every choice are in `PROGRESS.md`.

## Project Structure

```
hiver/
├── backend/           FastAPI app — Clean Architecture (domain / application / infrastructure / http)
│   ├── src/
│   │   ├── domain/            entities, value objects, errors, interfaces
│   │   ├── application/       use cases + DTOs
│   │   ├── infrastructure/    database (models, migrations 001–017, seed.py), http, payments, storage adapters
│   │   ├── shared/            config, security, DI container
│   │   └── main.py            FastAPI entrypoint
│   ├── tests/                 unit (domain) + use-case tests
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/          Vite + React + TypeScript
├── infra/             Prometheus / Grafana / (planned) Terraform + Helm
├── docs/              AI decisions log, architecture notes
├── PROGRESS.md        long-form project reference
├── CLAUDE.md          conventions for Claude Code contributors
├── docker-compose.yml
└── .env.example
```

## Getting Started

```bash
# 1. Environment variables
cp .env.example .env             # then set JWT_SECRET_KEY (see comment in the file)
# .env.example creds already match docker-compose; Stripe can stay as dummy values.

# 2. Start infra only — NOT the backend container.
#    (The backend container needs DB host = "postgres"; running it on the host needs
#     "localhost". The same .env can't satisfy both, so run the backend on the host.)
docker compose up -d postgres redis prometheus grafana

# 3. Backend deps + migrations + seed data
cd backend
pip install uv && uv sync --dev
alembic upgrade head

# 4. Dev server (auto-reload), from backend/
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

- API docs:  http://localhost:8000/docs
- Health:    http://localhost:8000/health
- Grafana:   http://localhost:3001 (admin/admin)

### Social login (optional)

Password login works out of the box. To enable Google/Facebook sign-in, set the OAuth
credentials in `.env` (see `.env.example`):

- **Google** — create an OAuth client (type *Web application*) at the
  [Google Cloud Console](https://console.cloud.google.com/apis/credentials) and add the
  redirect URI `http://localhost:8000/api/v1/auth/oauth/google/callback`.
- **Facebook** — add the *Facebook Login* product at
  [Meta for Developers](https://developers.facebook.com/apps) and set the valid OAuth redirect
  URI `http://localhost:8000/api/v1/auth/oauth/facebook/callback`.

Leave a provider's credentials blank to disable it (the login button returns a clear "not
configured" response instead of erroring).

### Shared cloud database & real services

To have the **whole team share one database** (no local Postgres) and to turn the
scaffolded integrations (Stripe, storage, maps, push) into real ones, see
[`docs/CLOUD_SETUP.md`](./docs/CLOUD_SETUP.md). Short version: point `DATABASE_URL` at a
Supabase project and set `DATABASE_USE_POOLER=true`.

## Development

```bash
cd backend
pip install uv
uv sync --dev
pre-commit install
pytest                          # tests not yet written (Phase 5)
```

```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

## API Endpoints (current)

> All feature endpoints are mounted under **`/api/v1`** (e.g. `POST /api/v1/auth/login`).
> `/health` stays at the root. The SPA's API base is `/api/v1` (override with `VITE_API_BASE`).

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET    | `/health` | – | Health check (root, no prefix) |
| POST   | `/auth/register` | – | Sign up — **rate-limited 5/min/IP** |
| POST   | `/auth/login` | – | Get JWT access + refresh — **rate-limited 10/min/IP** |
| POST   | `/auth/refresh` | – | Exchange refresh token for a fresh token pair |
| GET    | `/auth/oauth/{provider}/login` | – | Start Google/Facebook login (`?role=client\|hiver`) |
| GET    | `/auth/oauth/{provider}/callback` | – | Provider redirect → issues JWT, redirects to SPA |
| GET    | `/users/me` | Auth | Current authenticated user (role-aware) |
| POST   | `/tasks` | Client | Post a task |
| GET    | `/tasks` | Client | List my tasks (paginated) |
| GET    | `/tasks/search` | – | Public search: vertical, status, urgency, budget range |
| GET    | `/tasks/{id}` | – | Task details |
| POST   | `/tasks/{id}/start` | Hiver | Hiver moves task accepted → in_progress |
| POST   | `/tasks/{id}/complete` | Client | Client marks task done |
| POST   | `/tasks/{id}/cancel` | Client | Cancel a non-completed task |
| POST   | `/tasks/{id}/reviews` | Auth | Submit review (blind-reveal via DB trigger) |
| GET    | `/tasks/{id}/reviews` | – | List reviews on a task (revealed by default) |
| POST   | `/tasks/{id}/offers` | Hiver | Submit a bid |
| GET    | `/tasks/{id}/offers` | Client | List bids on my task |
| POST   | `/tasks/{id}/offers/{offer_id}/accept` | Client | Accept a bid |
| GET    | `/tasks/{id}/messages` | Auth | Chat thread (client + assigned hiver only) |
| POST   | `/tasks/{id}/messages` | Auth | Send a chat message (notifies the other party) |
| GET    | `/payments/tasks/{id}` | Auth | Escrow status for a task (client + assigned hiver) |
| POST   | `/payments/tasks/{id}/release` | Client | Release escrow to hiver |
| GET    | `/notifications` | Auth | In-app notification feed (Observer/EventBus) |
| GET    | `/notifications/unread_count` | Auth | Unread badge count (SPA polls this) |
| POST   | `/notifications/{id}/read` | Auth | Mark one notification read |
| POST   | `/notifications/read-all` | Auth | Mark all notifications read |
| GET    | `/users/{id}/reviews` | – | All revealed reviews received by user |
| GET    | `/users/clients/{id}` | – | Client profile |
| GET    | `/users/hivers/{id}` | – | Hiver profile |
| GET    | `/users/hivers/nearby` | – | PostGIS geo-search: `lat, lng, radius_km, vertical?` |
| PATCH  | `/users/hivers/me/availability` | Hiver | Toggle availability |

Escrow is now functional end-to-end via a mock payment adapter — accepting an offer holds
funds, completing releases them, cancelling refunds (swap to real Stripe by setting a live
`STRIPE_SECRET_KEY`; `payment_factory.get_payment_port` picks the adapter).

In-app notifications are live: use cases publish to a request-scoped `EventBus` (Observer) whose
subscriber persists to `notification_log`; the SPA polls the unread count and shows a bell.

Phase 5 (still to build): unit/integration tests, Prometheus dashboards, Kubernetes Helm chart, real Stripe webhook handler, Supabase Storage adapter, real push (FCM) adapter.

## Graded Subjects

| Subject | Focus |
|---|---|
| **РС** (Software Development) | Clean Architecture, REST API, error handling |
| **ООП** (OOP) | SOLID, polymorphism, design patterns (Repository, Strategy, Observer, Factory, Adapter, …) |
| **БД** (Databases) | 17 migrations, PL/pgSQL triggers, PostGIS `find_hivers_in_radius`, window-function view, Row Level Security |
| **ВОТ** (Virtualization & Cloud) | Multi-stage Docker, docker-compose, target K8s + Helm + Terraform + Prometheus |
