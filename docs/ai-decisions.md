# AI Decisions Log

Tracks every AI-generated code decision for the school defence.

## Format

```
### YYYY-MM-DD — <topic>
**Tool:** Claude Code
**Prompt:** <what was asked>
**Generated:** <summary of output>
**Accepted/Modified/Rejected:** <outcome>
**Reason:** <why>
**Learned:** <key insight>
```

---

### 2026-05-18 — Project scaffold (Phase 1)
**Tool:** Claude Code
**Prompt:** Generate Phase 1 project scaffold for Hiver FastAPI backend
**Generated:** Full folder structure, pyproject.toml, Dockerfile (multi-stage),
docker-compose.yml, .env.example, .gitignore, .pre-commit-config.yaml, README.md
**Accepted:** Yes — Clean Architecture folder layout matches course requirements
**Modified:** Added `docs/` folder for AI decisions log (mandatory for grade 6)
**Rejected approach:** Monolithic `app.py` entry point — rejected in favour of
`src/main.py` with layered package structure for ООП (OOP) grade requirements
**Learned:** Multi-stage Dockerfile with non-root user is required for ВОТ grade;
`uv` as package manager is faster than pip and produces a lockfile for reproducibility

---

### 2026-05-30 — Domain unit tests (Phase 5 start)
**Tool:** Claude Code
**Prompt:** Begin Phase 5 by writing unit tests for the domain layer
**Generated:** 97 tests across `backend/tests/unit/domain/` — value objects (Money
arithmetic/rounding/currency rules, Rating bounds + rolling average, WorkRadius tiers,
Location Haversine) and entity state machines (Task/Offer/Transaction transitions,
Review blind-reveal pair, User Client/Hiver polymorphism + XP level-ups). Added a
`conftest.py` that puts `src` on `sys.path`.
**Accepted:** Yes — tests assert real behaviour read from the source, not guesses; all green.
**Modified:** Ran with `-o addopts=""` because the project's pytest config enforces
`--cov-fail-under=80`, which fails a partial suite even when every test passes.
**Rejected approach:** Mocking value objects in entity tests — rejected; the domain is
pure Python and runs fast with real objects, so mocks would only hide behaviour.
**Learned:** The entities still call `datetime.utcnow()` (deprecated in 3.12). Flagged
for a deliberate projectwide migration to timezone-aware datetimes rather than a piecemeal
change, since it also touches the SQLAlchemy models and DTO serialization.
