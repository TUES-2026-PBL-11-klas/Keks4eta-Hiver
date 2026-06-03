from src.application.dtos.auth_dtos import LoginRequest, TokenResponse
from src.domain.errors.domain_errors import InvalidCredentialsError
from src.domain.interfaces.repositories import IClientRepository, IHiverRepository
from src.shared.security import create_access_token, create_refresh_token


class LoginUseCase:
    """
    SOLID S: only responsibility is authenticating a user.
    """

    def __init__(
        self,
        client_repo: IClientRepository,
        hiver_repo: IHiverRepository,
    ) -> None:
        self._client_repo = client_repo
        self._hiver_repo = hiver_repo

    async def execute(self, request: LoginRequest) -> TokenResponse:
        # Try client first, then hiver
        user = await self._client_repo.find_by_email(request.email)
        role = "client"

        if user is None:
            user = await self._hiver_repo.find_by_email(request.email)
            role = "hiver"

        if user is None or not user.verify_password(request.password):
            raise InvalidCredentialsError()

        return TokenResponse(
            access_token=create_access_token(user.id, role),
            refresh_token=create_refresh_token(user.id),
        )
