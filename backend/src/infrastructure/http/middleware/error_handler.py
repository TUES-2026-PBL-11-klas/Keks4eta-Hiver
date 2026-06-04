import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.domain.errors.domain_errors import AppError

logger = structlog.get_logger(__name__)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.code, "message": exc.message},
    )


async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": exc.errors(),
        },
    )


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Safety net: domain value objects (Money, Location, …) raise plain
    ValueError on invalid *user-supplied* input. Surface those as 422 instead
    of letting them fall through to a 500, but log them so they stay visible.
    """
    logger.warning("value_error", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code=422,
        content={"error": "VALIDATION_ERROR", "message": str(exc)},
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # Log with traceback — an unhandled 500 is a real bug we must be able to see.
    logger.error("unhandled_error", path=request.url.path, error=str(exc), exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_SERVER_ERROR", "message": "An unexpected error occurred"},
    )
