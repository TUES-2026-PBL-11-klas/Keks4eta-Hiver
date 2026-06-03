# HANDOFF — pick up here

> Living doc for the team. If you're resuming work (or someone ran out of AI usage), start here.
> **Last updated:** 2026-06-03 · **Branch:** `main` · **DB schema:** migration `017` (head, applied to shared Supabase).

---

## Where the project is right now

The full two-sided marketplace (M0–M7) is **done and merged to `main`**:

| Milestone | What it delivers | State |
|---|---|---|
| M0 | Pooler-safe Alembic migrations + seed (Supabase) | ✅ done |
| M1 | Escrow end-to-end via a **mock** payment adapter (hold on accept, refund on cancel) | ✅ done |
| M2 | Task image upload on **real Supabase Storage** | ✅ done (needs bucket + keys) |
| M3 | In-app notifications (Observer / EventBus) | ✅ done |
| M4 | Task chat between client and assigned hiver | ✅ done |
| M5 | Dispute resolution flow wired to escrow | ✅ done |
| M6 | Paid hiver visibility boosts (rank first in search) | ✅ done |
| M7 | Map on Nearby Hivers | ✅ done — **being upgraded to Google Maps (this session)** |

**This session (in progress):**
- Switch the Nearby-Hivers map from the free OSM iframe to **Google Maps** with a pin per hiver.
- Add **Google Places address autocomplete** to *Post a task* (stores real `lat/lng` on the task).
- Make **Google + Facebook login** real (code already exists — just needs credentials below).
- Refresh all docs (`README`, `PROGRESS`, `CLOUD_SETUP`, `.env.example`) to match reality.

**Backlog (not started):** M8 tests + green CI (mypy-strict, trufflehog) · M9 cloud deploy · Firebase push (still interface-only).

---

## Services & secrets to provision (DO THIS to make it fully work)

Local `.env` already has: `DATABASE_URL` (Supabase pooler), `DATABASE_USE_POOLER=true`, `JWT_SECRET_KEY`, `SUPABASE_URL`.
**Still missing — add these:**

| # | Service | Create | Env var(s) | Needs card? |
|---|---|---|---|---|
| 1 | **Google Cloud — OAuth** | APIs & Services → Credentials → *OAuth client ID* (Web app). Configure consent screen (External; add yourselves as test users). Redirect URI: `http://localhost:8000/api/v1/auth/oauth/google/callback` | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` → root `.env` | no |
| 2 | **Google Cloud — Maps** | Same project → enable **Maps JavaScript API** + **Places API (New)** → create a **browser API key**, restrict to HTTP referrers (`localhost:5173`, prod) + those 2 APIs. Enable **Billing** (attach card; free under demo limits). | `VITE_GOOGLE_MAPS_KEY` → **`frontend/.env`** | **yes** |
| 3 | **Meta / Facebook** | developers.facebook.com → create app → add **Facebook Login**. Redirect URI: `http://localhost:8000/api/v1/auth/oauth/facebook/callback`. Keep app in **Development mode** + add yourselves as testers (no review needed). | `FACEBOOK_CLIENT_ID`, `FACEBOOK_CLIENT_SECRET` → root `.env` | no |
| 4 | **Supabase Storage** | Storage → new **public** bucket `task-images`. Settings → API → copy the **service_role** key. | `SUPABASE_SERVICE_KEY` (and confirm `SUPABASE_URL`) → root `.env` | no |
| 5 | **Redis** | Local: already in `docker-compose` (nothing to do). Cloud: Upstash free → `REDIS_URL`. | `REDIS_URL` | no |
| — | ~~Stripe~~ | **Not needed** — escrow is a mock adapter. Leave `STRIPE_*` dummy. | — | — |

**GitHub repo secrets** — only for **cloud deploy (M9)**; CI (tests/lint) and local dev don't need them.
When you deploy, add under *repo → Settings → Secrets and variables → Actions*: `DATABASE_URL`, `JWT_SECRET_KEY`,
`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `FACEBOOK_CLIENT_ID`, `FACEBOOK_CLIENT_SECRET`, `SUPABASE_URL`,
`SUPABASE_SERVICE_KEY`, `VITE_GOOGLE_MAPS_KEY`, `REDIS_URL`, `OAUTH_REDIRECT_BASE_URL`, `FRONTEND_URL`, `CORS_ORIGINS`.
(Also add the **production** redirect URIs in the Google + Facebook consoles.)

---

## Pick up here (exact commands)

```powershell
# 1. Sync
git checkout main; git pull

# 2. Backend (from repo root; config reads ../.env automatically)
cd backend
uv sync --dev
uv run alembic upgrade head          # already at 017; no-op if current
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
#   API docs: http://localhost:8000/docs

# 3. Frontend (new terminal)
cd frontend
npm install                          # picks up @vis.gl/react-google-maps
#   Create frontend/.env with:  VITE_GOOGLE_MAPS_KEY=your_browser_key
npm run dev                          # http://localhost:5173
```

To enable each real feature: paste the matching secrets from the table above into the right `.env`,
then restart the affected process (backend for OAuth/Storage, frontend for the Maps key).

---

## Smoke test (is it really working?)

- **Login:** click Google / Facebook on `/login` → consent → you land authenticated; `/users/me` resolves.
- **Nearby Hivers:** Google map renders, "Use my location" recenters, a pin shows per hiver.
- **Post a task:** typing an address shows Google suggestions; picking one fills the address and saves `lat/lng`.
- **Image upload:** attaching an image to a task lands a file in the Supabase `task-images` bucket.
