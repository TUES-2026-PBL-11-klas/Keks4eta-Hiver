# Cloud Setup — Shared DB & Real Services

This guide covers (1) putting the database in the cloud so the **whole team shares one
database** (no local Postgres needed), and (2) what you must provision to turn each
"dummy" integration into a **real** one.

> **TL;DR of what's real today:** Auth (password + Google/Facebook OAuth), the full
> task/offer/review marketplace, **escrow** (mock payment adapter), **task chat**, **disputes**,
> **visibility boosts**, **image upload on real Supabase Storage**, and **Google Maps + Places**
> (map pins + address autocomplete) are all real. Only **push notifications** (FCM) remain
> interface-only — see [§3](#3-service-status--what-to-provision).

---

## 0. Get every key, step by step (and where to paste it)

Two env files hold secrets — neither is committed:
- **root `.env`** (backend) — copy from `.env.example` once: `cp .env.example .env`
- **`frontend/.env`** (browser) — copy from `frontend/.env.example`: `cp frontend/.env.example frontend/.env`

After editing `.env`, **restart the backend**; after editing `frontend/.env`, **restart `npm run dev`**
(Vite only reads env vars at startup).

### A. Google sign-in — `GOOGLE_CLIENT_ID` + `GOOGLE_CLIENT_SECRET` → root `.env`
1. Go to <https://console.cloud.google.com/> → create/select a project (top bar).
2. **APIs & Services → OAuth consent screen** → *External* → fill app name + your email → **Save**.
   Under *Test users*, **Add** the Google accounts you'll log in with (Dev mode needs this).
3. **APIs & Services → Credentials → + Create credentials → OAuth client ID** → Application type
   **Web application**.
4. Under **Authorized redirect URIs → Add URI**, paste exactly:
   `http://localhost:8000/api/v1/auth/oauth/google/callback` → **Create**.
5. Copy the **Client ID** and **Client secret** from the dialog into root `.env`:
   ```
   GOOGLE_CLIENT_ID=...apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=...
   ```

### B. Google Maps + Places — `VITE_GOOGLE_MAPS_KEY` → `frontend/.env`
1. Same Google Cloud project → **APIs & Services → Library** → enable **Maps JavaScript API**
   *and* **Places API** (search each, click *Enable*).
2. **Billing → Link a billing account** (a card is required even though a school-demo stays in the
   free tier and won't be charged).
3. **APIs & Services → Credentials → + Create credentials → API key**. Click the new key → **Edit**:
   - *Application restrictions* → **HTTP referrers** → add `http://localhost:5173/*` (and your prod URL).
   - *API restrictions* → **Restrict key** → tick **Maps JavaScript API** + **Places API** → **Save**.
4. Paste into `frontend/.env`:
   ```
   VITE_GOOGLE_MAPS_KEY=AIza...
   ```
   (No key? The map falls back to free OpenStreetMap and the location field becomes a plain input.)

### C. Facebook sign-in — `FACEBOOK_CLIENT_ID` + `FACEBOOK_CLIENT_SECRET` → root `.env`
1. <https://developers.facebook.com/apps> → **Create app** → use case *Authenticate and request data
   from users with Facebook Login* → finish.
2. In the app: **Add product → Facebook Login → Set up** (Web).
3. **Facebook Login → Settings → Valid OAuth Redirect URIs**, paste:
   `http://localhost:8000/api/v1/auth/oauth/facebook/callback` → **Save changes**.
4. **App settings → Basic**: copy **App ID** → `FACEBOOK_CLIENT_ID`, **App secret** (Show) →
   `FACEBOOK_CLIENT_SECRET` in root `.env`. Keep the app in **Development** mode and add yourselves
   under **App roles → Roles → Testers** (works without Meta review).

### D. Supabase Storage (task photos) — `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` → root `.env`
1. Supabase dashboard → **Storage → New bucket** → name **`task-images`** → tick **Public** → create.
2. **Project Settings → API**: copy **Project URL** → `SUPABASE_URL`, and the **`service_role`** key
   (under *Project API keys*, click reveal) → `SUPABASE_SERVICE_KEY` in root `.env`.
   > The `service_role` key bypasses RLS — keep it server-side only (it lives in the backend `.env`, never in `frontend/.env`).

### E. JWT signing secret — `JWT_SECRET_KEY` → root `.env`
Run `python -c "import secrets;print(secrets.token_hex(32))"` and paste the output:
```
JWT_SECRET_KEY=<64-hex-chars>
```

### Not needed for the demo
`STRIPE_*` stay dummy (escrow uses a mock adapter), `REDIS_URL` is already set for local Docker,
`GOOGLE_MAPS_API_KEY` (backend) and `FIREBASE_CREDENTIALS_JSON` stay blank.

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
- **Passwords with symbols:** prefer a DB password of only letters/digits. In a URL,
  characters like `$ ^ * % @ /` must be percent-encoded (`$`→`%24`, `%`→`%25`, …), and `$`
  also triggers `.env`/docker-compose variable substitution. `env.py` escapes `%` for
  Alembic's ConfigParser, but an alphanumeric password avoids the whole class of issues.

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

**GitHub Actions secrets (only for the CD deploy workflow — CI for tests/lint needs none):** add
under *repo → Settings → Secrets and variables → Actions* the same runtime values you put in `.env`:
`DATABASE_URL`, `JWT_SECRET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `FACEBOOK_CLIENT_ID`,
`FACEBOOK_CLIENT_SECRET`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `VITE_GOOGLE_MAPS_KEY`, `REDIS_URL`,
`OAUTH_REDIRECT_BASE_URL`, `FRONTEND_URL`, `CORS_ORIGINS` — plus `REGISTRY_USER`/`REGISTRY_PASSWORD`
for the image push. Add the **production** redirect URIs in the Google/Facebook consoles too.

---

## 3. Service status & what to provision

| Service | What it powers | Status in code | To make it real |
|---|---|---|---|
| **Google/Facebook OAuth** | Social login | ✅ **Implemented** (backend flow + frontend buttons) | Create OAuth apps, paste 4 env vars. See [§3.1](#31-googlefacebook-oauth-ready). |
| **Shared Postgres** | All data | ✅ **Implemented** (pooler-safe) | Supabase project + env (§1). |
| **Escrow** | Hold/release/refund payments | ✅ **Implemented** via a **mock** payment adapter (`payment_factory`) | Works out of the box; swap to Stripe only if you want real charges (§3.2). |
| **Supabase Storage** | Task image uploads | ✅ **Implemented** (`SupabaseStorageAdapter` + `POST /tasks/{id}/images`) | Create a `task-images` bucket + set `SUPABASE_*` (§3.3). |
| **Google Maps + Places** | Map pins on Nearby Hivers + address autocomplete on Post-a-task | ✅ **Implemented** (`@vis.gl/react-google-maps`; OSM fallback when keyless) | Browser key in `frontend/.env` (§3.4). |
| **Firebase** | Push notifications | ❌ **Interface only** (in-app notifications work; FCM does not) | Needs adapter + device tokens (§3.5). |

### 3.1 Google/Facebook OAuth (ready)
Already works — just provision credentials. Follow [§0.A](#a-google-sign-in--google_client_id--google_client_secret--root-env)
and [§0.C](#c-facebook-sign-in--facebook_client_id--facebook_client_secret--root-env), then restart the backend.

### 3.2 Escrow (already works — Stripe optional)
Escrow is **functional end-to-end on a mock payment adapter**: accepting an offer holds funds,
completing a task releases them, cancelling refunds, and a dispute locks the escrow. No account
needed. `payment_factory.get_payment_port()` selects the adapter, so to switch to **real** charges
you'd add a Stripe adapter there + a test `STRIPE_SECRET_KEY`/`STRIPE_WEBHOOK_SECRET` and a
`/payments/webhook` endpoint. (For real payouts to hivers: **Stripe Connect** + `stripe_account_id`.)

### 3.3 Supabase Storage (just provision the bucket)
The adapter + endpoint already exist (`SupabaseStorageAdapter`, `POST /api/v1/tasks/{id}/images`,
image picker on the task page). To turn it on:
1. Supabase → *Storage* → create a **public** bucket `task-images`.
2. Set `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` (service_role) in `.env`, restart the backend.

### 3.4 Google Maps + Places (just add a key)
The map ([NearbyHivers.tsx](../frontend/src/pages/NearbyHivers.tsx)) renders a pin per hiver and the
Post-a-task location field ([PostTask.tsx](../frontend/src/pages/PostTask.tsx)) has Places address
autocomplete that stores real coordinates on the task. To enable:
1. Google Cloud → enable **Maps JavaScript API** + **Places API** → create a **browser key**
   (restrict to your origins) → enable **billing** (free under demo limits).
2. Put `VITE_GOOGLE_MAPS_KEY=<key>` in **`frontend/.env`** (see `frontend/.env.example`).
   Without a key, the map falls back to a free OpenStreetMap embed and the field is a plain input.

### 3.5 Firebase push (needs adapter)
1. Firebase project → service account JSON → `FIREBASE_CREDENTIALS_JSON`.
2. Build an `IPushPort` adapter (FCM) + device-token registration + trigger on task/offer events.

---

## What I recommend doing now
1. **Shared DB (§1)** — biggest immediate win; unblocks the whole team. Needs only a Supabase project.
2. **OAuth (§3.1)** — already coded; just provision.
3. Then pick the next real integration (Stripe is the most impactful for a marketplace) and I'll
   build the wiring once you have the test keys.
