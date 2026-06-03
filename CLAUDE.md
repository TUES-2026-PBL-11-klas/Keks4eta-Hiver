# CLAUDE.md — Project Conventions for Claude Code

This file is loaded by every Claude Code session opened in this repo. Read once, follow always.

## 1. Documentation must stay in sync with code (MANDATORY)

After any code change that affects the surface area of the project, update the docs in the same turn — not as a follow-up:

| If you change... | Update... |
|------------------|-----------|
| Phase progress / commit a new feature | `README.md` status table + `PROGRESS.md` phase section |
| Add / remove an HTTP endpoint | `README.md` API table + `PROGRESS.md` endpoint summary |
| Add / change an env var | `README.md` env section + `.env.example` (root; backend) or `frontend/.env.example` (`VITE_*` browser vars) |
| Add / remove a dependency | `README.md` tech-stack table + `PROGRESS.md` stack table |
| Add / change a run/build command | `README.md` Getting Started |
| Add a domain entity / use case / pattern | `PROGRESS.md` design-patterns reference |

**Doc roles:**
- `README.md` — short entry point (≤200 lines). Status, quick-start, env, endpoint summary.
- `PROGRESS.md` — long-form reference. Full tech stack with rationales, phase deep-dives, design patterns, architecture decisions.
- `Hiver_Documentation.docx` — the formal Word document for school submission. Update when phase completes.

If you discover the docs are already stale (someone else made a change without updating them), fix the stale sections as part of your current task. Leaving rot in place compounds.

## 2. Architecture rules

This is Clean Architecture. Dependencies point inward only:

```
HTTP (routers)  →  Application (use cases)  →  Domain (entities)
                                                    ↑
                            Infrastructure  ────────┘ (implements domain interfaces)
```

- **Domain layer** (`backend/src/domain/`) imports nothing from `application` or `infrastructure`. Pure Python. No SQLAlchemy, no FastAPI, no Stripe.
- **Application layer** (`backend/src/application/`) imports only from `domain`. Never from `infrastructure`.
- **Infrastructure layer** (`backend/src/infrastructure/`) imports from `domain` interfaces. Wires concrete adapters.
- **HTTP layer** (`backend/src/infrastructure/http/`) wires DI in routers via `shared/container.py` factories.

If you catch a leak (e.g. a use case importing `PostgresXRepository`), fix it — don't merge.

**Frontend** (`frontend/src/`) is a responsive React + TypeScript SPA (Vite, React Router, Framer Motion). Keep its own layering clean:
- `lib/api.ts` — single fetch wrapper; base URL is `/api/v1` (override `VITE_API_BASE`). Don't call `fetch` directly elsewhere.
- `lib/services.ts` — typed service functions per resource; pages call services, never `api` or `fetch` directly.
- `context/AuthContext.tsx` — auth state, token storage, `loginWithProvider` (OAuth). Guard private routes with `components/ProtectedRoute`.
- `components/ui/` — shared primitives (Button, Card, Badge, Avatar, Stars, …). Reuse before adding new ones.
- Design tokens live in `index.css` (`--honey*`, `--ink*`, `--sp-*`, `--fs-*`); use them instead of hardcoded values. Build mobile-first, then layer breakpoints.
- Maps + geocoding go through **Google Maps + Places** (`@vis.gl/react-google-maps`), gated on `VITE_GOOGLE_MAPS_KEY`. Always keep a **keyless fallback** (OSM embed / plain input) so the app still runs without a key. Reuse `components/AddressAutocomplete.tsx` for address fields.

## 3. Database changes

- Schema changes go through Alembic migrations. Never edit the SQLAlchemy models in `backend/src/infrastructure/database/models/` without a matching migration in `backend/src/infrastructure/database/migrations/versions/`.
- Migrations are numbered `001_*.py` through `017_*.py` (currently). Add the next sequential number.
- PostGIS `Geography` columns must use raw `op.execute()` SQL (GeoAlchemy2 doesn't work inside `op.create_table()`).
- Migration predicates must stay `IMMUTABLE` — never use `NOW()` in a partial-index `WHERE` (Postgres rejects it; see the 013 fix). Filter on time at query time instead.
- Seed data lives in `backend/src/infrastructure/database/seed.py`.

## 4. Testing

- Domain entities + value objects: unit tests, no mocks needed (pure code).
- Use cases: unit tests with in-memory fake repositories.
- Repositories: integration tests against a real test database (Docker-spun Postgres).
- API: end-to-end HTTP tests with FastAPI's `TestClient`.

## 5. Commits

- No Claude co-author trailer (configured globally).
- Commit messages: present-tense subject line, optional body explaining *why*.
- One logical change per commit. No "WIP" or "stuff" commits on `main`.

## 6. School grading context (light — don't gate work on it)

This is a school project nominally graded across 4 subjects. Treat the list below as **context, not
a checklist**: prioritise making features actually work and the code clean over mapping every change
to a subject. For reference only:
- **РС** (Software Development): clean code, REST API, architecture
- **ООП** (OOP): SOLID, inheritance, polymorphism, design patterns
- **БД** (Databases): migrations, stored procedures, triggers, views, PostGIS
- **ВОТ** (Virtualization & Cloud): Docker, K8s, CI/CD, monitoring
