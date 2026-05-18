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
