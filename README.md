# Hiver

A two-sided task marketplace — clients post real-world tasks (cleaning, tutoring, tech help, moving, etc.) and **hivers** bid on them. Built as a school project, graded across 4 subjects.

> **Full reference:** see [`PROGRESS.md`](./PROGRESS.md) for the deep-dive (tech rationales, phase breakdowns, design patterns, gap analysis).
> **Defending the project?** [`docs/DEFENCE.md`](./docs/DEFENCE.md) is the revise-from-this guide: what the site is, why each tech was chosen, and per-subject talking points + likely questions for РС / ООП / БД / ВОТ.
> **For Claude Code contributors:** see [`CLAUDE.md`](./CLAUDE.md) for repo conventions (Clean Architecture rules, doc-sync rule).

## Phase Status

| Phase | Description | Status | Commit |
|---|---|---|---|
| 1 | Project scaffold | ✅ Done | `bfab23f` |
| 2 | Domain layer (OOP) | ✅ Done | `05b3bd1` |
| 3 | Database migrations + seed | ✅ Done | `c12b244` |
| 4 | API layer (FastAPI routers + DI) | ✅ Done | `b0b0447` |
| 5 | Tests + CI/CD + observability | ✅ Done — 294 unit tests + use-case + HTTP integration tests (green); GitHub Actions CI (ruff + mypy --strict + pytest≥80% cov + pip-audit + trufflehog + Docker build); Prometheus `/metrics` wired + Grafana datasource auto-provisioned | — |
| 6 | Responsive frontend + social login | ✅ Done — full responsive web app, all endpoints wired, Google/Facebook OAuth | — |
| 7 | Marketplace completion | ✅ Done — escrow (mock adapter) ✅, in-app notifications (Observer/EventBus) ✅, task chat ✅, disputes ✅, visibility boosts ✅, Supabase Storage image upload ✅, shared Supabase DB + RLS ✅, Google Maps + Places (map pins + address autocomplete) ✅, unified accounts ✅, tasks-on-map search ✅, profile editing + settings (avatar, bio, skills, service location) ✅, favorites (save tasks/hivers) ✅, task promotion (pay-to-feature) ✅, chat inbox (conversations list + unread) ✅ | — |
| 8 | Cloud deploy | 🔄 In progress — Helm chart + CD workflow written; **needs a cluster + registry/secrets to actually deploy** (see "Deployment" below) | — |

## Tech Stack (short)

| Layer | Choice |
|---|---|
| Language | Python 3.12 |
| Backend | FastAPI + Pydantic v2 + Uvicorn |
| ORM | SQLAlchemy 2.0 (async) + asyncpg |
| Migrations | Alembic (22 chained) |
| Database | PostgreSQL 16 + PostGIS |
| Cache | Redis 7 — backs the auth rate limiter (slowapi storage) + `/health` probe; in-memory fallback when absent |
| Auth | JWT (python-jose) + pwdlib (Argon2, bcrypt fallback); social login via Authlib (Google + Facebook) |
| Payments | Escrow via a **mock** payment adapter by default (swap to Stripe manual-capture via `payment_factory`) |
| Storage | Supabase Storage (task images + profile avatars); Pillow validates image integrity before upload |
| Maps | Google Maps + Places (`@vis.gl/react-google-maps`) — task pins on Find-tasks & hiver pins on Nearby Hivers, address autocomplete on Post-a-task; keyless OSM fallback |
| Frontend | React 19 + TypeScript 5 + Vite 8 + Framer Motion (responsive web app) |
| Container | Docker (multi-stage, non-root, <150 MB) + docker-compose |
| Infra | Kubernetes Helm chart (`infra/k8s/charts/hiver`); Terraform skeleton (`infra/terraform`) |
| Observability | Prometheus (scrapes app `/metrics`) + Grafana (datasource auto-provisioned) |
| CI/CD | GitHub Actions — CI on PRs (lint/type/test/security/docker), CD on push-to-main (Helm deploy; needs cluster) |
| Package mgr | `uv` (Python), `npm` (frontend) |

Rationales for every choice are in `PROGRESS.md`.

## Project Structure

```
hiver/
├── backend/           FastAPI app — Clean Architecture (domain / application / infrastructure / http)
│   ├── src/
│   │   ├── domain/            entities, value objects, errors, interfaces
│   │   ├── application/       use cases + DTOs
│   │   ├── infrastructure/    database (models, migrations 001–022, seed.py), http, payments, storage adapters
│   │   ├── shared/            config, security, DI container
│   │   └── main.py            FastAPI entrypoint
│   ├── tests/                 unit (domain + use-case) + HTTP integration tests
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/          Vite + React + TypeScript
├── infra/             Prometheus + Grafana, Kubernetes Helm chart, Terraform skeleton
├── docs/              defence prep, cloud setup, AI decisions log
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

### Maps & location (optional)

The Nearby-Hivers map and the Post-a-task address autocomplete use **Google Maps + Places**.
Create `frontend/.env` (see [`frontend/.env.example`](./frontend/.env.example)) with a browser key:

```
VITE_GOOGLE_MAPS_KEY=your_browser_key
```

Provision it in the [Google Cloud Console](https://console.cloud.google.com/): enable **Maps
JavaScript API** + **Places API**, create a browser key (restrict it to your origins), and enable
billing (a school-demo stays within the free tier). Without the key, the map falls back to a free
OpenStreetMap embed and the location field becomes a plain text input — the app still runs.

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
ruff check src && mypy src --strict          # lint + types (CI gates on these)
pytest tests/unit -q --no-cov                # 294 fast unit tests (no DB needed)
pytest --cov=src --cov-fail-under=80         # full suite incl. HTTP integration (needs the Postgres + Redis containers up)
```

```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

## API Endpoints (current)

> All feature endpoints are mounted under **`/api/v1`** (e.g. `POST /api/v1/auth/login`).
> `/health` stays at the root. The SPA's API base is `/api/v1` (override with `VITE_API_BASE`).

> **Unified accounts:** every account is both a client and a hiver. The
> `Client`/`Hiver` labels below now indicate which *facet* an action uses, not a
> separate account type — any authenticated user can call them.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET    | `/health` | – | Health check (root, no prefix) |
| GET    | `/metrics` | – | Prometheus metrics (root, no prefix; request count/latency by handler) |
| POST   | `/auth/register` | – | Sign up — creates a unified account (client + hiver); **rate-limited 5/min/IP** |
| POST   | `/auth/login` | – | Get JWT access + refresh — **rate-limited 10/min/IP** |
| POST   | `/auth/refresh` | – | Exchange refresh token for a fresh token pair |
| GET    | `/auth/oauth/{provider}/login` | – | Start Google/Facebook login (role param accepted but ignored) |
| GET    | `/auth/oauth/{provider}/callback` | – | Provider redirect → issues JWT, redirects to SPA |
| GET    | `/users/me` | Auth | Current authenticated user — both client + hiver facets (incl. service location) |
| PATCH  | `/users/me` | Auth | Edit own profile (full_name, phone, bio, skills, work_radius_km, lat/lng + display) — partial |
| POST   | `/users/me/avatar` | Auth | Upload a profile photo (Pillow-validated, ≤3 MB) → Supabase Storage |
| POST   | `/tasks` | Client | Post a task |
| GET    | `/tasks` | Client | List tasks I posted (paginated) |
| GET    | `/tasks/assigned` | Hiver | List tasks assigned to me (jobs I'm doing) |
| GET    | `/tasks/search` | – | Public search: `vertical, status, is_urgent, min_budget, max_budget, q` (free-text), `lat/lng/radius_km` (PostGIS), `sort=recent\|distance\|budget` — results carry `latitude/longitude` for map pins |
| GET    | `/tasks/{id}` | – | Task details |
| POST   | `/tasks/{id}/start` | Hiver | Hiver moves task accepted → in_progress |
| POST   | `/tasks/{id}/complete` | Client | Client marks task done |
| POST   | `/tasks/{id}/cancel` | Client | Cancel a non-completed task |
| POST   | `/tasks/{id}/boost` | Client | Pay to feature the task atop search for 7 days (mock-charged) |
| POST   | `/tasks/{id}/images` | Client | Upload a task photo to Supabase Storage |
| POST   | `/tasks/{id}/reviews` | Auth | Submit review (blind-reveal via DB trigger) |
| GET    | `/tasks/{id}/reviews` | – | List reviews on a task (revealed by default) |
| POST   | `/tasks/{id}/offers` | Hiver | Submit a bid |
| GET    | `/tasks/{id}/offers` | Client | List bids on my task |
| POST   | `/tasks/{id}/offers/{offer_id}/accept` | Client | Accept a bid |
| GET    | `/tasks/{id}/messages` | Auth | Chat thread (client + assigned hiver only) |
| POST   | `/tasks/{id}/messages` | Auth | Send a chat message (notifies the other party) |
| GET    | `/conversations` | Auth | Chat inbox — one row per task thread (last message + unread) |
| GET    | `/tasks/{id}/disputes` | Auth | The task's dispute, if any (participants only) |
| POST   | `/tasks/{id}/disputes` | Auth | Open a dispute — locks escrow as `disputed` |
| POST   | `/tasks/{id}/disputes/resolve` | Auth | Resolve by concession (client→release, hiver→refund) |
| GET    | `/payments/tasks/{id}` | Auth | Escrow status for a task (client + assigned hiver) |
| POST   | `/payments/tasks/{id}/release` | Client | Release escrow to hiver |
| GET    | `/notifications` | Auth | In-app notification feed (Observer/EventBus) |
| GET    | `/notifications/unread_count` | Auth | Unread badge count (SPA polls this) |
| POST   | `/notifications/{id}/read` | Auth | Mark one notification read |
| POST   | `/notifications/read-all` | Auth | Mark all notifications read |
| GET    | `/users/{id}/reviews` | – | All revealed reviews received by user |
| GET    | `/users/clients/{id}` | – | Client profile |
| GET    | `/users/hivers/{id}` | – | Hiver profile |
| GET    | `/users/hivers/nearby` | – | PostGIS geo-search: `lat, lng, radius_km, vertical?` (boosted hivers rank first) |
| PATCH  | `/users/hivers/me/availability` | Hiver | Toggle availability |
| POST   | `/users/hivers/me/boost` | Hiver | Buy a visibility boost (mock-charged, 7 days) |
| GET    | `/users/hivers/me/boost` | Hiver | My active boost, if any |
| POST   | `/favorites` | Auth | Save a task or hiver (`target_type`, `target_id`) — idempotent |
| DELETE | `/favorites/{target_type}/{target_id}` | Auth | Unsave a task or hiver |
| GET    | `/favorites/tasks` | Auth | My saved tasks |
| GET    | `/favorites/hivers` | Auth | My saved hivers |
| GET    | `/favorites/ids` | Auth | Saved id sets per type (SPA fills hearts from this) |

Escrow is now functional end-to-end via a mock payment adapter — accepting an offer holds
funds, completing releases them, cancelling refunds (swap to real Stripe by setting a live
`STRIPE_SECRET_KEY`; `payment_factory.get_payment_port` picks the adapter).

In-app notifications are live: use cases publish to a request-scoped `EventBus` (Observer) whose
subscriber persists to `notification_log`; the SPA polls the unread count and shows a bell.

Task image uploads are live on **real Supabase Storage** (`POST /tasks/{id}/images` → public
`task-images` bucket; owners add photos from the task page).

**Still scaffolded (not production-wired):** real Stripe charges + webhook handler (mock adapter is the default), real push/FCM (in-app notifications work today), and the actual cloud deploy (chart + CD exist — see Deployment).

## Observability

`docker compose up` brings up Prometheus (`:9090`), Alertmanager (`:9093`) and Grafana (`:3001`,
admin/admin). The backend exposes **`/metrics`** (via `prometheus-fastapi-instrumentator`);
Prometheus scrapes the compose `backend` service, evaluates the rules in
`infra/prometheus/alerts.yml`, and routes firing alerts to Alertmanager. Grafana auto-provisions
the Prometheus datasource **and** a ready dashboard ("Hiver — Backend Overview": uptime, request
rate, error-rate %, avg + p50/p95/p99 latency, status-class breakdown, top endpoints). To see
metrics flow, run the backend **as the compose service**
(`docker compose up backend`) so the `backend:8000` target resolves — the host-run dev server
(Getting Started) is reachable at `localhost:8000` but not at the `backend` hostname Prometheus uses.

## Deployment

CI/CD is GitHub Actions:
- **CI** (`.github/workflows/ci.yml`) runs on PRs to `main`/`develop`: ruff, `mypy --strict`,
  `pytest --cov-fail-under=80` (with Postgres + Redis services), `pip-audit`, trufflehog, and a
  Docker build with a <150 MB size gate.
- **CD** (`.github/workflows/cd.yml`) runs on push to `main`: builds + pushes the image and runs
  `helm upgrade --install` against the chart in `infra/k8s/charts/hiver`.

To make CD actually deploy you must provide: a container registry (`REGISTRY_USER` /
`REGISTRY_PASSWORD` repo secrets), a Kubernetes cluster the runner can reach (add a kubeconfig /
cluster-auth step to `cd.yml`), and a `hiver-secrets` Secret in the cluster holding `DATABASE_URL`,
`REDIS_URL`, `JWT_SECRET_KEY`, `STRIPE_*` (e.g. `kubectl create secret generic hiver-secrets
--from-env-file=.env`). Validate the chart locally with `helm lint infra/k8s/charts/hiver` and
`helm template hiver infra/k8s/charts/hiver`.

## Graded Subjects

| Subject | Focus |
|---|---|
| **РС** (Software Development) | Clean Architecture, REST API, error handling |
| **ООП** (OOP) | SOLID, polymorphism, design patterns (Repository, Strategy, Observer, Factory, Adapter, …) |
| **БД** (Databases) | 22 migrations, PL/pgSQL triggers, PostGIS `find_hivers_in_radius`, window-function view, Row Level Security |
| **ВОТ** (Virtualization & Cloud) | Multi-stage Docker (<150 MB, non-root), docker-compose, Kubernetes Helm chart (Deployment/Service/HPA/Ingress), GitHub Actions CI/CD, Prometheus `/metrics` + Grafana, Terraform skeleton |
