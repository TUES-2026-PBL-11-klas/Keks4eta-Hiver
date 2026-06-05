from __future__ import annotations

import uuid

from src.application.dtos.auth_dtos import OAuthUserInfo, TokenResponse
from src.domain.entities.user import Client, Hiver
from src.domain.interfaces.repositories import IClientRepository, IHiverRepository
from src.domain.value_objects.rating import Rating
from src.domain.value_objects.work_radius import WorkRadius
from src.shared.security import create_access_token, create_refresh_token


class OAuthLoginUseCase:
    """
    Logs a user in via a social provider (Google/Facebook).

    SOLID S: sole responsibility is turning verified provider identity into
    an authenticated session, creating or linking the account as needed.
    SOLID D: depends only on repository interfaces, not on Postgres or Authlib.

    Resolution order:
      1. Known provider identity  -> log that user in.
      2. Same email, password account -> link the provider to it (one identity).
      3. Brand-new -> create a passwordless account in the requested role.
    """

    def __init__(
        self,
        client_repo: IClientRepository,
        hiver_repo: IHiverRepository,
    ) -> None:
        self._client_repo = client_repo
        self._hiver_repo = hiver_repo

    async def execute(self, info: OAuthUserInfo) -> TokenResponse:
        # 1. Already linked to this provider identity?
        client = await self._client_repo.find_by_oauth(info.provider, info.oauth_id)
        if client is not None:
            return self._tokens(client.id, "client")

        hiver = await self._hiver_repo.find_by_oauth(info.provider, info.oauth_id)
        if hiver is not None:
            return self._tokens(hiver.id, "hiver")

        # 2. Existing password account with the same email -> link it.
        existing_client = await self._client_repo.find_by_email(info.email)
        if existing_client is not None:
            existing_client.oauth_provider = info.provider
            existing_client.oauth_id = info.oauth_id
            if existing_client.avatar_url is None and info.avatar_url:
                existing_client.avatar_url = info.avatar_url
            await self._client_repo.save(existing_client)
            return self._tokens(existing_client.id, "client")

        existing_hiver = await self._hiver_repo.find_by_email(info.email)
        if existing_hiver is not None:
            existing_hiver.oauth_provider = info.provider
            existing_hiver.oauth_id = info.oauth_id
            if existing_hiver.avatar_url is None and info.avatar_url:
                existing_hiver.avatar_url = info.avatar_url
            await self._hiver_repo.save(existing_hiver)
            return self._tokens(existing_hiver.id, "hiver")

        # 3. Brand-new passwordless account — create BOTH facets (unified
        #    accounts), sharing one users row. The client save creates the user
        #    + links the provider identity; the hiver save adds the hiver row.
        user_id = str(uuid.uuid4())
        await self._client_repo.save(
            Client(
                id=user_id,
                email=info.email,
                _password_hash=None,
                full_name=info.full_name,
                avatar_url=info.avatar_url,
                oauth_provider=info.provider,
                oauth_id=info.oauth_id,
                rating_as_client=Rating(5.0),
            )
        )
        await self._hiver_repo.save(
            Hiver(
                id=user_id,
                email=info.email,
                _password_hash=None,
                full_name=info.full_name,
                avatar_url=info.avatar_url,
                oauth_provider=info.provider,
                oauth_id=info.oauth_id,
                work_radius=WorkRadius.default(),
            )
        )
        return self._tokens(user_id, "client")

    @staticmethod
    def _tokens(user_id: str, role: str) -> TokenResponse:
        return TokenResponse(
            access_token=create_access_token(user_id, role),
            refresh_token=create_refresh_token(user_id),
        )
