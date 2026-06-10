from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from typing import Any

import redis.asyncio as redis_async
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import ValidationError
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.sessions import SessionMiddleware

from src.domain.errors.domain_errors import AppError
from src.infrastructure.database.session import engine
from src.infrastructure.http.middleware.error_handler import (
    app_error_handler,
    unhandled_error_handler,
    validation_error_handler,
    value_error_handler,
)
from src.infrastructure.http.rate_limit import limiter
from src.infrastructure.http.routers import (
    auth,
    disputes,
    favorites,
    messages,
    notifications,
    offers,
    payments,
    tasks,
    users,
)
from src.shared.config import settings

# Async Redis client for the /health connectivity probe. Lazy — only connects on
# first use; a short timeout keeps /health fast even if Redis is down.
redis_client = redis_async.from_url(settings.redis_url, socket_connect_timeout=1)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Ensure the task-images bucket exists when storage is configured.
    from src.infrastructure.storage.storage_factory import (
        TASK_IMAGES_BUCKET,
        get_storage_port,
    )

    storage = get_storage_port()
    if storage is not None:
        # Don't block startup on storage availability.
        with suppress(Exception):
            await storage.ensure_bucket(TASK_IMAGES_BUCKET, public=True)
    yield
    await engine.dispose()
    with suppress(Exception):
        await redis_client.aclose()


app = FastAPI(
    title="Hiver API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Short-lived signed cookie used only to carry OAuth state/nonce + chosen role
# across the provider round-trip. Not used for app authentication (JWT does that).
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.jwt_secret_key,
    same_site="lax",
    https_only=settings.app_env == "production",
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(ValidationError, validation_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(ValueError, value_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, unhandled_error_handler)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(tasks.router, prefix=settings.api_prefix)
app.include_router(offers.router, prefix=settings.api_prefix)
app.include_router(users.router, prefix=settings.api_prefix)
app.include_router(payments.router, prefix=settings.api_prefix)
app.include_router(notifications.router, prefix=settings.api_prefix)
app.include_router(messages.router, prefix=settings.api_prefix)
app.include_router(disputes.router, prefix=settings.api_prefix)
app.include_router(favorites.router, prefix=settings.api_prefix)

# Prometheus metrics at /metrics (request count/latency/in-progress by handler).
# This is the target the bundled Prometheus config scrapes (infra/prometheus).
Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, Any]:
    """Liveness + Redis connectivity (the cache/rate-limit store)."""
    redis_ok = False
    with suppress(Exception):
        redis_ok = bool(await redis_client.ping())
    return {"status": "ok", "version": "0.1.0", "redis": "up" if redis_ok else "down"}
