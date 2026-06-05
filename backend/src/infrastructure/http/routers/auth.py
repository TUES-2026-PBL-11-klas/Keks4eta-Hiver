from urllib.parse import urlencode

from fastapi import APIRouter, Path, Query, Request
from fastapi.responses import RedirectResponse

from src.infrastructure.http.dependencies import SessionDep
from src.infrastructure.http.rate_limit import limiter
from src.infrastructure.http.oauth import oauth, is_provider_configured, SUPPORTED_PROVIDERS
from src.infrastructure.database.repositories.user_repository import (
    PostgresClientRepository,
    PostgresHiverRepository,
)
from src.application.use_cases.auth.register_use_case import RegisterUseCase
from src.application.use_cases.auth.login_use_case import LoginUseCase
from src.application.use_cases.auth.refresh_token_use_case import RefreshTokenUseCase
from src.application.use_cases.auth.oauth_login_use_case import OAuthLoginUseCase
from src.application.dtos.auth_dtos import (
    RegisterRequest,
    LoginRequest,
    RefreshRequest, 
    OAuthUserInfo,
    TokenResponse,
)
from src.domain.errors.domain_errors import (
    OAuthProviderNotConfiguredError,
    OAuthError,
)
from src.shared.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

ProviderPath = Path(..., description="OAuth provider", pattern="^(google|facebook)$")


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


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("30/minute")
async def refresh(request: Request, body: RefreshRequest, session: SessionDep) -> TokenResponse:
    use_case = RefreshTokenUseCase(
        client_repo=PostgresClientRepository(session),
        hiver_repo=PostgresHiverRepository(session),
    )
    return await use_case.execute(body.refresh_token)


# ── Social login (Google / Facebook) ────────────────────────────────────────

@router.get("/oauth/{provider}/login")
async def oauth_login(
    request: Request,
    provider: str = ProviderPath,
    role: str = Query("client", pattern="^(client|hiver)$"),
) -> RedirectResponse:
    """Kick off the OAuth flow — redirects the browser to the provider's consent screen."""
    if not is_provider_configured(provider):
        raise OAuthProviderNotConfiguredError(provider)
    # Role for first-time accounts survives the round-trip in the signed session.
    request.session["oauth_role"] = role
    base = settings.oauth_redirect_base_url.rstrip("/")
    redirect_uri = f"{base}{settings.api_prefix}/auth/oauth/{provider}/callback"
    client = oauth.create_client(provider)
    return await client.authorize_redirect(request, redirect_uri)


@router.get("/oauth/{provider}/callback")
async def oauth_callback(
    request: Request,
    session: SessionDep,
    provider: str = ProviderPath,
) -> RedirectResponse:
    """Provider redirects here. Exchange the code, resolve the user, hand tokens to the SPA."""
    if not is_provider_configured(provider):
        raise OAuthProviderNotConfiguredError(provider)

    client = oauth.create_client(provider)
    try:
        token = await client.authorize_access_token(request)
        info = await _extract_user_info(provider, client, token)
    except OAuthError:
        raise
    except Exception:  # token exchange / provider errors -> bounce to login
        return RedirectResponse(f"{settings.frontend_url}/login?error=oauth_failed")

    role = request.session.pop("oauth_role", "client")
    info.role = role  # type: ignore[assignment]

    use_case = OAuthLoginUseCase(
        client_repo=PostgresClientRepository(session),
        hiver_repo=PostgresHiverRepository(session),
    )
    tokens = await use_case.execute(info)

    # Tokens go in the URL fragment so they never hit the backend/proxy access logs.
    fragment = urlencode(
        {"access_token": tokens.access_token, "refresh_token": tokens.refresh_token}
    )
    return RedirectResponse(f"{settings.frontend_url}/auth/callback#{fragment}")


async def _extract_user_info(provider: str, client, token) -> OAuthUserInfo:
    """Normalize the provider-specific userinfo payload into our DTO."""
    if provider == "google":
        data = token.get("userinfo")
        if data is None:
            data = (await client.userinfo(token=token))
        email = data.get("email")
        if not email:
            raise OAuthError("Google account has no email")
        return OAuthUserInfo(
            provider="google",
            oauth_id=str(data["sub"]),
            email=email,
            full_name=data.get("name") or email.split("@")[0],
            avatar_url=data.get("picture"),
        )

    # Facebook
    resp = await client.get("me?fields=id,name,email,picture.type(large)", token=token)
    data = resp.json()
    email = data.get("email")
    if not email:
        raise OAuthError("Facebook account has no email (grant the email permission)")
    picture = (data.get("picture") or {}).get("data", {}).get("url")
    return OAuthUserInfo(
        provider="facebook",
        oauth_id=str(data["id"]),
        email=email,
        full_name=data.get("name") or email.split("@")[0],
        avatar_url=picture,
    )


__all__ = ["router", "SUPPORTED_PROVIDERS"]
