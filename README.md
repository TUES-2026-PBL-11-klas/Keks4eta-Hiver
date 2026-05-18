# Hiver

A two-sided micro-services marketplace connecting clients with everyday needs to skilled executors ("hivers").

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Python 3.12 |
| ORM | SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Database | PostgreSQL 16 + PostGIS |
| Cache | Redis 7 |
| Auth | JWT (python-jose) + bcrypt |
| Payments | Stripe (Test Mode) |
| Storage | Supabase Storage |
| Containerization | Docker + Docker Compose |
| Infra | Terraform + Kubernetes (Helm) |
| Observability | Prometheus + Grafana |

## Project Structure

```
hiver/
├── backend/        FastAPI application (Clean Architecture)
├── frontend/       React Native / Expo app
├── infra/          Terraform, Helm, Prometheus, Grafana
├── docs/           AI decisions log, architecture diagrams
├── docker-compose.yml
└── .env.example
```

## Getting Started

### 1. Copy environment variables
```bash
cp .env.example .env
# Fill in all required values
```

### 2. Start services
```bash
docker compose up -d
```

### 3. Run migrations
```bash
cd backend
alembic upgrade head
```

### 4. Start dev server
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: http://localhost:8000/docs

## Development

```bash
cd backend
pip install uv
uv sync --dev
pre-commit install
pytest
```

## Phases

| Phase | Description | Status |
|---|---|---|
| 1 | Project scaffold | Done |
| 2 | Domain layer (OOP) | Pending |
| 3 | Database migrations | Pending |
| 4 | API layer | Pending |
| 5 | Tests + CI/CD + Infra | Pending |
