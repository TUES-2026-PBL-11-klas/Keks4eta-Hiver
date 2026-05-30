from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

from src.shared.config import settings
from src.infrastructure.database.session import engine
from src.infrastructure.http.middleware.error_handler import (
    app_error_handler,
    validation_error_handler,
    unhandled_error_handler,
)
from src.infrastructure.http.rate_limit import limiter
from src.domain.errors.domain_errors import AppError
from src.infrastructure.http.routers import auth
from src.infrastructure.http.routers import tasks
from src.infrastructure.http.routers import offers
from src.infrastructure.http.routers import users
from src.infrastructure.http.routers import payments


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="Hiver API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(ValidationError, validation_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)

app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(offers.router)
app.include_router(users.router)
app.include_router(payments.router)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
