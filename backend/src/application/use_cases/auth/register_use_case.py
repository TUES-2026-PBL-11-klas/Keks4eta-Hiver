from __future__ import annotations

import uuid

from src.application.dtos.auth_dtos import RegisterRequest, TokenResponse
from src.domain.entities.user import Client, Hiver
from src.domain.errors.domain_errors import DuplicateEmailError
from src.domain.interfaces.repositories import IClientRepository, IHiverRepository
from src.domain.value_objects.rating import Rating
from src.domain.value_objects.work_radius import WorkRadius
from src.shared.password import hash_password
from src.shared.security import create_access_token, create_refresh_token


class RegisterUseCase:
    """
    SOLID S: only responsibility is registering a new user.
    SOLID D: depends on repository interfaces, not Postgres directly.
    """

    def __init__(
        self,
        client_repo: IClientRepository,
        hiver_repo: IHiverRepository,
    ) -> None:
        self._client_repo = client_repo
        self._hiver_repo = hiver_repo

    async def execute(self, request: RegisterRequest) -> TokenResponse:
        # Check for duplicate email across both roles
        existing_client = await self._client_repo.find_by_email(request.email)
        existing_hiver = await self._hiver_repo.find_by_email(request.email)
        if existing_client or existing_hiver:
            raise DuplicateEmailError(request.email)

        user_id = str(uuid.uuid4())
        password_hash = hash_password(request.password)

        if request.role == "client":
            client = Client(
                id=user_id,
                email=request.email,
                _password_hash=password_hash,
                full_name=request.full_name,
                phone=request.phone,
                rating_as_client=Rating(5.0),
            )
            await self._client_repo.save(client)
        else:
            hiver = Hiver(
                id=user_id,
                email=request.email,
                _password_hash=password_hash,
                full_name=request.full_name,
                phone=request.phone,
                work_radius=WorkRadius.default(),
            )
            await self._hiver_repo.save(hiver)

        return TokenResponse(
            access_token=create_access_token(user_id, request.role),
            refresh_token=create_refresh_token(user_id),
        )
