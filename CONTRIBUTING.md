# Contributing to Hiver

This is a school project graded across four subjects: **РС, ООП, БД, ВОТ**.
Treat the repo as production-style — clean commits, clear PRs, docs kept in sync.

## Workflow

1. Branch from `main`: `feat/<scope>`, `fix/<scope>`, `docs/<scope>`, `chore/<scope>`.
2. Read `CLAUDE.md` once — it covers Clean Architecture rules, DB rules, doc-sync rules.
3. Make the change, run the checks below.
4. Update the docs in the same PR (see *Doc-sync* below).
5. Open a PR using the template — it auto-loads when you click "Create PR".

## Local checks (must pass before requesting review)

Backend:
```bash
cd backend
uv run ruff check src/
uv run mypy src/ --strict
uv run pytest
```

Frontend:
```bash
cd frontend
npm run lint
npm run build
```

## Doc-sync (non-negotiable)

If your change touches any of these, update the matching doc **in the same PR**:

| Change | Doc to update |
|---|---|
| New / removed endpoint | `README.md` (API table) |
| New env var | `README.md` + `.env.example` |
| New install/run script | `README.md` (Getting started) |
| Phase finished / commit hash | `PROGRESS.md` + `README.md` (Phase table) |
| User-facing flow or architecture | `Hiver_Documentation.docx` |

PRs that skip doc-sync get sent back. This rule exists because the README is what teachers and teammates land on first.

## Commit messages

Imperative, present tense, scope-prefixed:

```
phase 4: add /tasks/search endpoint with vertical+budget filters
fix(auth): bcrypt rounds raised to 12 to match prod config
docs: regenerate Hiver_Documentation.docx after Phase 4
```

Group related changes into one commit per logical step — not one commit per file.

## Architecture rules (short version — full version in `CLAUDE.md`)

- Domain layer has **zero** framework imports (no SQLAlchemy, no FastAPI, no Pydantic).
- Use cases live in `application/use_cases/`, take repositories via constructor injection.
- Concrete repos live in `infrastructure/database/repositories/`, implement domain interfaces.
- HTTP routers are thin: parse DTO → call use case → return DTO. No business logic.
- Every DB schema change = new Alembic migration. Never edit an applied migration.

## Reporting bugs / requesting features

Use the issue templates — they prompt for the context reviewers actually need (phase, subject, repro steps).

## Code of conduct

Be kind. We're all learning. Disagreements about technical choices go in the PR thread, not in DMs.
