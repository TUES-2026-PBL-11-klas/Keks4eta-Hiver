# Canva deck prompt — Hiver defence presentation

Paste the block below into **Canva → Magic Design / "Docs to Deck" / Magic Write for presentations**
(or the "Generate a presentation" prompt box). It produces a ~16-slide defence deck for the school
project, with the most depth on **OOP (ООП)** and **Databases (БД)**. After generating, apply the
brand colours/fonts in the *Style note* at the bottom.

---

## PROMPT (copy everything between the lines)

---

Create a **16-slide technical presentation** for a school software-engineering defence of a project
called **Hiver** — a two-sided local-services marketplace (clients post real-world tasks: cleaning,
tutoring, tech help, moving, pet care; vetted "hivers" bid on them). The project is graded across
four subjects: **РС** (Software Development), **ООП** (OOP), **БД** (Databases), **ВОТ**
(Virtualization & Cloud). Audience: teachers + peers. Tone: confident, concrete, engineering-focused.
Give **OOP and Databases the most detail (2 slides each)**. Use short bullet points, not paragraphs.
Include the speaker notes I provide under each slide.

**Slide 1 — Title.** "Hiver — a local-services marketplace." Subtitle: "Clean Architecture · FastAPI ·
PostgreSQL/PostGIS · React · Docker/Kubernetes." Add the team name and "Graded: РС · ООП · БД · ВОТ."
Speaker note: one-sentence pitch — "Hiver connects people who need everyday tasks done with nearby
helpers, with escrow-protected payments and map-based discovery."

**Slide 2 — The problem.** Finding a trustworthy local helper today means scattered Facebook groups,
no reputation, no payment protection, no way to see who's nearby. Bullets: fragmented · no trust
signals · no escrow · no location matching. Speaker note: motivate why a dedicated marketplace matters.

**Slide 3 — The solution & value.** A single app where clients post a task, nearby hivers send offers,
the client accepts one, pays into **escrow**, the hiver does the work, funds release on completion.
Bullets: reputation (blind reviews) · escrow protection · PostGIS proximity search · in-app chat ·
unified account (everyone is both client and hiver). Speaker note: the "happy path" in one breath.

**Slide 4 — How it works (flow).** A horizontal flow: Post task → Offers → Accept (escrow holds) →
Chat → Start → Complete (escrow releases) → Blind reviews. Speaker note: mention disputes (escrow
locks) and paid visibility boosts.

**Slide 5 — Architecture (РС).** "Clean Architecture — dependencies point inward only." Show four
layers as concentric or stacked boxes: **HTTP (FastAPI routers/middleware) → Application (use cases +
DTOs) → Domain (entities + value objects, pure Python) ← Infrastructure (DB, storage, payments
adapters implement domain interfaces)**. Bullets: domain imports nothing external · DI wired in
routers via a container of factories · testable in isolation. Speaker note: explain why the domain
has zero framework imports (swap DB/Stripe without touching business rules).

**Slide 6 — OOP: SOLID in practice (ООП, 1/2).** One principle per bullet with a concrete example:
- **S** — each use case does one thing (`CreateTaskUseCase`, `ReleaseEscrowUseCase`).
- **O** — new payment/notification providers add an adapter, no edits to use cases.
- **L** — every `IStoragePort` adapter (Supabase, mock) is substitutable.
- **I** — small focused interfaces (`ITaskRepository`, `IPaymentPort`, `IStoragePort`).
- **D** — use cases depend on domain interfaces, not concrete classes.
Speaker note: point out dependency inversion is what makes the mock-vs-real payment swap trivial.

**Slide 7 — OOP: Design patterns (ООП, 2/2).** A 2-column table "Pattern → Where in Hiver":
- **Repository** → `PostgresTaskRepository`, `PostgresHiverRepository` (hide SQL/PostGIS behind interfaces)
- **Strategy / Adapter** → `IPaymentPort` with `MockPaymentAdapter` & `StripeAdapter`; `IStoragePort` → `SupabaseStorageAdapter`
- **Factory** → `payment_factory`, `storage_factory`, `TaskFactory` (build the right object per config/vertical)
- **Observer (Event Bus)** → use cases publish domain events; an in-app-notification subscriber reacts
- **Builder** → vertical-specific task builders assemble tasks with smart-answer questions
- **Value Object** → immutable `Money`, `Location`, `Rating`, `WorkRadius` (validation + behaviour inside)
Speaker note: emphasise the Observer/EventBus — it decouples "something happened" from "notify the user."

**Slide 8 — Databases: schema & PostGIS (БД, 1/2).** "PostgreSQL 16 + PostGIS, 22 Alembic migrations."
Bullets: core tables (users, clients, hivers, tasks, offers, transactions/escrow, reviews, messages,
disputes, boosts, notifications, favorites) · **`Geography(POINT, 4326)`** columns for hiver & task
location · a **PL/pgSQL stored function `find_hivers_in_radius(lat,lng,radius)`** using `ST_DWithin`/
`ST_Distance` for proximity search · schema is migration-versioned (source of truth, never hand-edited).
Speaker note: show one ST_DWithin query and explain SRID 4326 = GPS coordinates.

**Slide 9 — Databases: triggers, views, security (БД, 2/2).** Bullets:
- **Triggers** — blind-review reveal (reviews stay hidden until both sides submit), auto `updated_at`.
- **Window-function view** — `hiver_earnings_monthly` (per-hiver monthly earnings via SQL window functions).
- **Row-Level Security** — default-deny RLS (migration 017) so Supabase's auto API can't bypass the backend.
- **Pooler-safe** — runs through pgbouncer (transaction pooler) with prepared-statement caching disabled.
Speaker note: RLS is the defence-in-depth answer to "what if someone hits the DB directly?"

**Slide 10 — Tech stack (РС).** Two columns. Backend: Python 3.12 · FastAPI · Pydantic v2 ·
SQLAlchemy 2 (async) + asyncpg · Alembic · Redis · JWT + Argon2 (pwdlib) · Authlib (Google/Facebook).
Frontend: React 19 · TypeScript 5 · Vite 8 · React Router · Framer Motion · Google Maps + Places
(keyless OSM fallback). Speaker note: note auto-generated OpenAPI docs and end-to-end type safety.

**Slide 11 — Virtualization & Cloud (ВОТ).** Bullets: **multi-stage, non-root Docker image (<150 MB)**
· `docker-compose` (Postgres/PostGIS, Redis, Prometheus, Alertmanager, Grafana, backend) ·
**Kubernetes Helm chart** (Deployment/Service/HPA/Ingress) · **GitHub Actions CI** (ruff + mypy
--strict + pytest ≥80% coverage + pip-audit + trufflehog + Docker build) and **CD** (Helm deploy).
Speaker note: explain why metrics need the backend in compose (Prometheus scrapes the `backend` host).

**Slide 12 — Observability & monitoring (ВОТ).** Bullets: Prometheus scrapes `/metrics` (auto-
instrumented FastAPI) · Grafana with an auto-provisioned datasource + dashboard · Alertmanager for
alerts · structured JSON logging (structlog). Add a simple "app → /metrics → Prometheus → Grafana"
diagram. Speaker note: this is the ВОТ "production-readiness" story.

**Slide 13 — Security.** Bullets: JWT access+refresh (rotation) · Argon2 password hashing ·
rate-limiting on auth endpoints · OAuth 2.0 / OIDC (Google + Facebook) with signed session state ·
**escrow** holds funds until completion · **RLS** default-deny · image-upload validation (Pillow).
Speaker note: tie escrow + reviews + RLS together as the "trust" layer.

**Slide 14 — Live demo flow.** A screenshot strip / numbered steps: sign in → post a task with map
address autocomplete → see hivers on the map → send/accept an offer → chat → complete → release
escrow → leave a review. Speaker note: have the app running; this is the moment to show, not tell.

**Slide 15 — Per-subject takeaways.** Four quadrants, one line each:
- **РС** — Clean Architecture, typed REST API, layered + testable.
- **ООП** — SOLID + 6 design patterns, immutable value objects, polymorphic adapters.
- **БД** — PostGIS geo-search, PL/pgSQL triggers & functions, window-function view, RLS, 22 migrations.
- **ВОТ** — Docker, Kubernetes/Helm, CI/CD, Prometheus + Grafana monitoring.
Speaker note: this slide maps every grading criterion to concrete evidence.

**Slide 16 — Closing / roadmap.** "Built to extend." Bullets: real Stripe checkout (adapter ready) ·
FCM push notifications (interface ready) · admin dispute console · Bulgarian i18n. End with a thank-you
+ the repo/QR. Speaker note: confident close — the architecture makes each of these a small, isolated add.

Make the design clean and modern: generous whitespace, one accent colour, simple icons, and a
consistent header/footer. Prefer diagrams over walls of text on the architecture, OOP-patterns,
database, and observability slides.

---

## Style note (apply in Canva after generating)

- **Colours:** primary accent **honey `#EE7F22`**, ink/text **deep navy `#00224F`**, background warm
  paper **`#FBEFE0`**, cards white `#FFFFFF`. Use honey sparingly for emphasis/CTAs.
- **Fonts:** display/headings **Fraunces** (serif), body **Hanken Grotesk** (sans), code/labels/numbers
  **Space Mono**.
- **Motif:** hexagon / honeycomb accents (the "Hive" brand). Keep it editorial and uncluttered.
- For the architecture, OOP-pattern, DB-schema, and observability slides, use Canva's diagram/table
  elements rather than plain bullets.
