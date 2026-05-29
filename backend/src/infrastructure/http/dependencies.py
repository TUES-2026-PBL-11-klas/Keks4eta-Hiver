from typing import AsyncGenerator, Annotated
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.session import AsyncSessionLocal
from src.shared.security import decode_token
from src.domain.errors.domain_errors import InvalidTokenError, UnauthorizedActionError
from src.infrastructure.database.repositories.user_repository import (
    PostgresClientRepository,
    PostgresHiverRepository,
)
from src.domain.entities.user import Client, Hiver


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        async with session.begin():
            yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user_payload(
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise InvalidTokenError()
    token = authorization.removeprefix("Bearer ")
    return decode_token(token)


UserPayloadDep = Annotated[dict, Depends(get_current_user_payload)]


async def get_current_client(
    payload: UserPayloadDep,
    session: SessionDep,
) -> Client:
    if payload.get("role") != "client":
        raise UnauthorizedActionError("access client-only resource")
    client = await PostgresClientRepository(session).find_by_id(payload["sub"])
    if client is None:
        raise UnauthorizedActionError("access this resource")
    return client


async def get_current_hiver(
    payload: UserPayloadDep,
    session: SessionDep,
) -> Hiver:
    if payload.get("role") != "hiver":
        raise UnauthorizedActionError("access hiver-only resource")
    hiver = await PostgresHiverRepository(session).find_by_id(payload["sub"])
    if hiver is None:
        raise UnauthorizedActionError("access this resource")
    return hiver


ClientDep = Annotated[Client, Depends(get_current_client)]
HiverDep = Annotated[Hiver, Depends(get_current_hiver)]
