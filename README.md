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

## Tech Stack (short)

| Layer | Choice |
|---|---|
| Language | Python 3.12 |
| Backend | FastAPI + Pydantic v2 + Uvicorn |
| ORM | SQLAlchemy 2.0 (async) + asyncpg |
| Migrations | Alembic (15 chained) |
| Database | PostgreSQL 16 + PostGIS |
| Cache | Redis 7 |
| Auth | JWT (python-jose) + passlib[bcrypt] |
| Payments | Stripe (manual capture for escrow) |
| Storage | Supabase Storage (task images) |
| Frontend | React 18 + TypeScript 5 + Vite 5 |
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
│   │   ├── infrastructure/    database, http, payments, storage adapters
│   │   ├── shared/            config, security, DI container
│   │   └── main.py            FastAPI entrypoint
│   ├── alembic/               migrations 001–015 + seeds
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

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET    | `/health` | – | Health check |
| POST   | `/auth/register` | – | Sign up — **rate-limited 5/min/IP** |
| POST   | `/auth/login` | – | Get JWT access + refresh — **rate-limited 10/min/IP** |
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
| POST   | `/payments/tasks/{id}/release` | Client | Release escrow to hiver |
| GET    | `/users/{id}/reviews` | – | All revealed reviews received by user |
| GET    | `/users/clients/{id}` | – | Client profile |
| GET    | `/users/hivers/{id}` | – | Hiver profile |
| GET    | `/users/hivers/nearby` | – | PostGIS geo-search: `lat, lng, radius_km, vertical?` |
| PATCH  | `/users/hivers/me/availability` | Hiver | Toggle availability |

Phase 5 (still to build): unit/integration tests, Prometheus dashboards, Kubernetes Helm chart, real Stripe webhook handler, Supabase Storage adapter, notification adapter.

## Graded Subjects

| Subject | Focus |
|---|---|
| **РС** (Software Development) | Clean Architecture, REST API, error handling |
| **ООП** (OOP) | SOLID, polymorphism, design patterns (Repository, Strategy, Observer, Factory, Adapter, …) |
| **БД** (Databases) | 15 migrations, PL/pgSQL triggers, PostGIS `find_hivers_in_radius`, window-function view |
| **ВОТ** (Virtualization & Cloud) | Multi-stage Docker, docker-compose, target K8s + Helm + Terraform + Prometheus |
