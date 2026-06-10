# Hiver — Demo script & "turn on the scaffolds" guide

Two parts: **A.** how to demo the app live, **B.** how to activate everything that's currently a
scaffold (Stripe, push, K8s deploy, Terraform).

---

## A. How to demo the project

### A0. Pre-flight (5 min before)
```powershell
# infra (Postgres+PostGIS, Redis, Prometheus, Alertmanager, Grafana)
docker compose up -d postgres redis prometheus grafana alertmanager
# backend on the host
cd backend; uv sync; uv run alembic upgrade head; uv run python -m src.infrastructure.database.seed
uv run uvicorn src.main:app --reload --port 8000
# frontend (new terminal)
cd frontend; npm install; npm run dev          # http://localhost:5173
```
For the **full** experience set the keys first (see CLOUD_SETUP §0): `VITE_GOOGLE_MAPS_KEY`
(frontend/.env), Google/Facebook OAuth + `SUPABASE_*` (root .env). Without them the map falls back to
OpenStreetMap and login uses email/password — still fully demoable.

> Open **two browsers** (or one + an incognito window) so you can play **client** and **hiver** at the
> same time. Have the seed data loaded so there's something on the map.

### A1. The happy-path story (what to click + say)
1. **Landing → sign up / Google login** as user A. *"One account is both a client and a hiver."*
2. **Post a task** → start typing an address → **Google Places autocomplete** picks real coordinates →
   pick a category, budget → post. *"The address becomes a real point on the map."*
3. **User B (2nd browser)** → **Find tasks** → the task shows as a **pin on the map** → open it → **send
   an offer**.
4. **User A** → open the task → **see the offer + the offerer's profile/rating** → **Accept**. *"Accepting
   holds the money in escrow."* (Escrow status flips to **held**.)
5. **Chat** opens between them → type a message → it appears **live** in the other browser (WebSocket).
6. **User B** → **Start task**; **User A** → **Mark complete** → **Release escrow**. *"Funds release to the
   hiver; the platform keeps its fee."*
7. Both **leave a review** → they stay hidden until both submit, then **reveal together** (a DB trigger).
8. Show the breadth: **Nearby Hivers** map, **Favorites** (save a task/hiver), **Boost** (pay-to-feature),
   the **notifications bell**, the **Inbox** (conversations).
9. **Under the hood (impressive finish):**
   - `http://localhost:8000/docs` — auto-generated **Swagger** API.
   - `http://localhost:8000/health` — `{"status":"ok","redis":"up"}` (live Redis).
   - **Grafana** `http://localhost:3001` (admin/admin) → *Hiver — Backend Overview* dashboard updating
     live; `http://localhost:8000/metrics` is the raw Prometheus feed.
   - Hammer login 11× in a minute → **429 Too Many Requests** (Redis-backed rate limit); show the key:
     `docker compose exec redis redis-cli -a redis_password KEYS 'hiver-rl*'`.

### A2. If something's offline
- No Google key → map shows OpenStreetMap, location is a plain text box. Fine.
- No Redis → `/health` shows `redis: down`, rate limiting falls back to in-memory. Fine.
- No `SUPABASE_*` → image upload returns a clean "storage not configured" 503. Skip that step.

---

## B. Turning on the scaffolded integrations

Each of these is written behind an interface and **off by default** — turning it on is configuration +
(for push) one adapter class. Ordered cheapest-first.

### B1. Live keys (maps, social login, image storage) — *config only*
Follow **`docs/CLOUD_SETUP.md` §0** step-by-step: Google Maps + Places → `frontend/.env`; Google +
Facebook OAuth and Supabase Storage (bucket `task-images` + service_role key) → root `.env`. Restart
the affected process. Nothing to code.

### B2. Real Stripe payments — *config only (adapter already written)*
`payment_factory.get_payment_port()` returns the **mock** adapter until a *real* `sk_…` key is present,
then it returns the existing `StripeAdapter` (`infrastructure/payments/stripe_adapter.py`).
1. Stripe test dashboard → copy a real test **`STRIPE_SECRET_KEY`** (and `STRIPE_WEBHOOK_SECRET`) into
   root `.env`.
2. Restart the backend — escrow hold/release/refund now run through Stripe PaymentIntents (manual
   capture). *Remaining for production-grade:* add a `POST /payments/webhook` endpoint to confirm
   intents asynchronously, and **Stripe Connect** to actually pay out hivers (`stripe_account_id`).

### B3. Push notifications (FCM) — *one adapter class*
In-app notifications already work (`InAppNotificationAdapter` → `notification_log`). For phone push:
1. Firebase project → service-account JSON → set **`FIREBASE_CREDENTIALS_JSON`** (already a config
   field).
2. Add `firebase-admin` to `backend/pyproject.toml`.
3. Write `FcmNotificationAdapter(INotificationPort)` next to `in_app_adapter.py` (implement `send` /
   `send_bulk` via FCM), add a device-token table + register endpoint, and fan out to **both** adapters
   on notify. The `INotificationPort` interface means no use case changes.

### B4. Cloud deploy / CD (Kubernetes) — *infra + secrets*
The Helm chart (`infra/k8s/charts/hiver`) and `.github/workflows/cd.yml` (registry login → `helm
upgrade --install`) are complete; deploying for real needs:
1. A **Kubernetes cluster** (managed: GKE/EKS/AKS/DigitalOcean, or local `kind`/`minikube` for a demo).
2. Repo **Actions secrets**: `REGISTRY_USER`, `REGISTRY_PASSWORD` (image registry).
3. A **cluster-auth step** in `cd.yml` before the Helm step (e.g. `azure/aks-set-context` or write a
   `KUBECONFIG` from a secret).
4. The app secrets as a K8s Secret:
   `kubectl create secret generic hiver-secrets --from-env-file=.env`.
5. Push to `main` → CD builds the image and runs `helm upgrade --install hiver
   infra/k8s/charts/hiver`. Validate locally first: `helm lint infra/k8s/charts/hiver`.

### B5. Terraform (Infrastructure as Code) — *fill in the skeleton*
`infra/terraform/` has `environments/prod/main.tf` + `modules/{networking,database}`. To use it: add a
remote state backend (e.g. S3 + DynamoDB lock), flesh out the module resources for your cloud, then
`terraform init && terraform plan && terraform apply`. (Optional — only needed for a cloud demo.)

### B6. Managed Redis (prod) — *config only*
Create a free **Upstash** Redis, set **`REDIS_URL`** to its URL. The rate limiter + `/health` use it
automatically; no code change.
