from fastapi import APIRouter, Request

from src.infrastructure.http.dependencies import SessionDep
from src.infrastructure.http.rate_limit import limiter
from src.infrastructure.database.repositories.user_repository import (
    PostgresClientRepository,
    PostgresHiverRepository,
)
from src.application.use_cases.auth.register_use_case import RegisterUseCase
from src.application.use_cases.auth.login_use_case import LoginUseCase
from src.application.dtos.auth_dtos import RegisterRequest, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
@limiter.limit("5/minute")
async def register(request: Request, body: RegisterRequest, session: SessionDep) -> TokenResponse:
    use_case = RegisterUseCase(
        client_repo=PostgresClientRepository(session),
        hiver_repo=PostgresHiverRepository(session),
    )
    return await use_case.execute(body)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest, session: SessionDep) -> TokenResponse:
    use_case = LoginUseCase(
        client_repo=PostgresClientRepository(session),
        hiver_repo=PostgresHiverRepository(session),
    )
    return await use_case.execute(body)
