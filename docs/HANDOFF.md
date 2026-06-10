# HANDOFF — pick up here

> Quick "resume here" for the team. For the full project reference see [`PROGRESS.md`](../PROGRESS.md);
> for the defence write-up see [`docs/DEFENCE.md`](./DEFENCE.md).

## Status

Phases 1–7 done and merged to `main` (full marketplace: tasks/offers/reviews, escrow on a mock
adapter, in-app notifications, chat + inbox, disputes, boosts, Supabase Storage image upload, Google
Maps + Places, favorites, task promotion). Phase 8 (cloud deploy) is scaffolded (Helm chart + CD
workflow) but needs a cluster + secrets. DB schema is at migration **022**.

## Run it locally

```powershell
git checkout main; git pull

# Backend (host dev; config reads ../.env automatically)
cd backend; uv sync
uv run alembic upgrade head                 # applies any new migrations to the shared Supabase DB
uv run uvicorn src.main:app --reload --port 8000     # API docs → http://localhost:8000/docs

# Frontend (new terminal)
cd frontend; npm install
npm run dev                                 # http://localhost:5173
```

## Keys / secrets

All API keys (Google sign-in, Google Maps, Facebook, Supabase Storage, JWT) — **step-by-step click
paths and exactly where to paste each** — are in
[`docs/CLOUD_SETUP.md` §0](./CLOUD_SETUP.md#0-get-every-key-step-by-step-and-where-to-paste-it).
Restart the backend after editing root `.env`; restart `npm run dev` after editing `frontend/.env`.

## Grafana / metrics

Prometheus scrapes the `backend` **container** (hostname `backend`), not your host dev server — so to
see metrics flow, run the backend in compose:

```powershell
docker compose up -d postgres redis prometheus grafana backend
# Grafana    → http://localhost:3001  (admin/admin) — Prometheus datasource auto-provisioned
# Prometheus → http://localhost:9090   ·   raw metrics → http://localhost:8000/metrics
```

## Smoke test

- **Login:** Google / Facebook on `/login` → consent → land authenticated; `/users/me` resolves.
- **Nearby Hivers / Find tasks:** the map renders with pins; "Use my location" recenters.
- **Post a task:** typing an address shows Google suggestions; picking one saves `lat/lng`.
- **Task photos:** upload an image, then remove it with the ✕ on the photo.
- **Dashboard:** posted tasks under *Your tasks*; accepted jobs under *Jobs you're doing*.
