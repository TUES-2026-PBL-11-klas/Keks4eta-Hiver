# Cloud Setup — Shared DB & Real Services

This guide covers (1) putting the database in the cloud so the **whole team shares one
database** (no local Postgres needed), and (2) what you must provision to turn each
"dummy" integration into a **real** one.

> **TL;DR of what's real today:** Auth (password + Google/Facebook OAuth) and the full
> task/offer/review marketplace are real and work against any Postgres. Payments, image
> storage, maps, and push notifications are **scaffolded but not wired to live services
> yet** — see [§3](#3-service-status--what-to-provision).

---

## 1. Shared cloud database (do this first)

Goal: one Postgres everyone connects to, instead of a container per laptop.

**Recommended: Supabase** (free, hosted Postgres **with PostGIS**, so migrations/triggers/
views all work). Neon or Railway work too; steps are analogous.

### Steps
1. Create a project at <https://supabase.com> (set a strong DB password, pick a nearby region).
2. **Enable PostGIS:** Dashboard → *Database → Extensions* → enable `postgis`.
   (Migration `001` also runs `CREATE EXTENSION postgis`; enabling it first avoids permission edge-cases.)
3. Get the connection string: Dashboard → *Connect* → **Transaction pooler** (port `6543`).
   It looks like:
   ```
   postgresql://postgres.<ref>:<PASSWORD>@aws-0-<region>.pooler.supabase.com:6543/postgres
   ```
4. In each teammate's `.env`, set (note the `+asyncpg` driver and the pooler flag):
   ```
   DATABASE_URL=postgresql+asyncpg://postgres.<ref>:<PASSWORD>@aws-0-<region>.pooler.supabase.com:6543/postgres
   DATABASE_USE_POOLER=true
   ```
   `DATABASE_USE_POOLER=true` makes the app pgbouncer-safe (no app-side pool, no asyncpg
   prepared-statement cache) — see [session.py](../backend/src/infrastructure/database/session.py).
5. Run migrations **once** (any one teammate):
   ```powershell
   cd backend; uv run alembic upgrade head
   ```
6. Done — everyone now reads/writes the same database. You can stop running the local
   `postgres` container (still run Redis locally, or use a hosted Redis like Upstash).

### Notes
- **Direct vs pooler:** Supabase's *direct* connection (`db.<ref>.supabase.co:5432`) is
  IPv6-only on the free tier and keeps prepared statements; the **transaction pooler**
  (6543) is IPv4-friendly and is the right default for this app — hence `DATABASE_USE_POOLER`.
- **Migrations are the schema source of truth.** Don't edit tables in the Supabase UI; add an
  Alembic migration (project rule, see `CLAUDE.md`).
- **Browsing:** use the Supabase Table Editor, or connect DBeaver to the pooler URL.

---

## 2. Deploying to the cloud (optional, for a live demo)

A cheap/free stack that fits this repo:

| Piece | Where | Notes |
|---|---|---|
| **Database** | Supabase (above) | shared Postgres + PostGIS |
| **Backend** (FastAPI) | Fly.io / Railway / Render | uses the existing multi-stage `backend/Dockerfile`; set the same env vars |
| **Frontend** (Vite) | Vercel / Netlify | build `npm run build`, output `frontend/dist`; set `VITE_API_BASE` to the backend's public URL |
| **Redis** | Upstash (free) | set `REDIS_URL` |
| **Metrics** | the included Prometheus/Grafana, or Grafana Cloud | infra under `infra/` |

Production hardening already in place / worth setting:
- Set `APP_ENV=production` (enables secure session cookie for OAuth, disables SQL echo).
- Set `CORS_ORIGINS` to your deployed frontend URL (comma-separated for multiple).
- Set `OAUTH_REDIRECT_BASE_URL` and `FRONTEND_URL` to the public backend/frontend URLs, and
  add those redirect URIs in the Google/Facebook consoles.
- A Kubernetes Helm chart + Terraform skeleton exist under `infra/` for the K8s target.

---

## 3. Service status & what to provision

| Service | What it powers | Status in code | To make it real |
|---|---|---|---|
| **Google/Facebook OAuth** | Social login | ✅ **Implemented** (backend flow + frontend buttons) | Create OAuth apps, paste 4 env vars. See [§3.1](#31-googlefacebook-oauth-ready). |
| **Shared Postgres** | All data | ✅ **Implemented** (pooler-safe) | Supabase project + env (§1). |
| **Stripe (escrow)** | Hold/release payments | ⚠️ **Partial** — `StripeAdapter` written but **not wired**; no PaymentIntent is created on offer-accept; no webhook | Needs code (§3.2) + Stripe account. |
| **Supabase Storage** | Task image uploads | ❌ **Interface only** (`IStoragePort`, empty `storage/`) | Needs adapter + upload endpoint (§3.3) + bucket. |
| **Google Maps** | Map on "Nearby hivers" | ❌ **Unused** env var; UI shows a list | Needs Maps JS key + embed (§3.4). |
| **Firebase** | Push notifications | ❌ **Interface only** | Needs adapter + device tokens (§3.5). |

### 3.1 Google/Facebook OAuth (ready)
Already works — just provision credentials. See the **Social login** section of [README.md](../README.md):
create the OAuth apps, add the callback URIs, and set `GOOGLE_CLIENT_ID/SECRET`,
`FACEBOOK_CLIENT_ID/SECRET` in `.env`. Restart the backend.

### 3.2 Stripe escrow (needs wiring)
What's missing to make payments real:
1. A test Stripe account → `STRIPE_SECRET_KEY` (test mode), `STRIPE_WEBHOOK_SECRET`.
2. Wire `StripeAdapter` through DI with a real Stripe client (today no use case receives it).
3. Create a `PaymentIntent` (manual capture) + a `transactions` row when a client **accepts an
   offer** (the escrow *hold*). Currently `ReleaseEscrowUseCase` only flips a domain status and
   will 404 if no transaction exists.
4. Capture on release (`release_payment`), refund on cancel, and add a `/payments/webhook`
   endpoint to confirm intents.
5. For real payouts to hivers, **Stripe Connect** (onboard hivers, `stripe_account_id`).
   *I can build all of this — it needs your test Stripe keys to verify end-to-end.*

### 3.3 Supabase Storage (needs adapter)
1. Supabase → *Storage* → create a bucket `task-images`.
2. `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` in `.env`.
3. Build a `SupabaseStorageAdapter(IStoragePort)` + `POST /api/v1/tasks/{id}/images` use case,
   and an image picker on PostTask/TaskDetail.

### 3.4 Google Maps (needs embed)
1. Google Cloud → enable *Maps JavaScript API* → create a browser key → `VITE_GOOGLE_MAPS_KEY`.
2. Replace the list-only view in [NearbyHivers.tsx](../frontend/src/pages/NearbyHivers.tsx) with a
   map showing hiver pins (the PostGIS search already returns coords/distance).

### 3.5 Firebase push (needs adapter)
1. Firebase project → service account JSON → `FIREBASE_CREDENTIALS_JSON`.
2. Build an `IPushPort` adapter (FCM) + device-token registration + trigger on task/offer events.

---

## What I recommend doing now
1. **Shared DB (§1)** — biggest immediate win; unblocks the whole team. Needs only a Supabase project.
2. **OAuth (§3.1)** — already coded; just provision.
3. Then pick the next real integration (Stripe is the most impactful for a marketplace) and I'll
   build the wiring once you have the test keys.
