from __future__ import annotations

from src.application.dtos.auth_dtos import TokenResponse
from src.domain.errors.domain_errors import InvalidTokenError
from src.domain.interfaces.repositories import IClientRepository, IHiverRepository
from src.shared.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)


class RefreshTokenUseCase:
    """
    Exchanges a valid refresh token for a fresh access + refresh token pair.

    SOLID S: sole responsibility is rotating tokens.
    The refresh token carries no role, so the user's current role is resolved
    from the repositories (the source of truth) on every refresh.
    """

    def __init__(
        self,
        client_repo: IClientRepository,
        hiver_repo: IHiverRepository,
    ) -> None:
        self._client_repo = client_repo
        self._hiver_repo = hiver_repo

    async def execute(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise InvalidTokenError()

        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenError()

        role = "client"
        user = await self._client_repo.find_by_id(user_id)
        if user is None:
            user = await self._hiver_repo.find_by_id(user_id)
            role = "hiver"
        if user is None:
            raise InvalidTokenError()

        return TokenResponse(
            access_token=create_access_token(user_id, role),
            refresh_token=create_refresh_token(user_id),
        )
