"""Social-login provider registry (Authlib).

Infrastructure only — the rest of the app never imports Authlib. Providers are
registered lazily and only when their credentials are configured, so the app
boots fine with social login disabled (the router returns a clear 4xx instead
of a 500 when an unconfigured provider is hit).
"""
from __future__ import annotations

from authlib.integrations.starlette_client import OAuth

from src.shared.config import settings

SUPPORTED_PROVIDERS = ("google", "facebook")

oauth = OAuth()

if settings.google_client_id and settings.google_client_secret:
    oauth.register(
        name="google",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

if settings.facebook_client_id and settings.facebook_client_secret:
    oauth.register(
        name="facebook",
        client_id=settings.facebook_client_id,
        client_secret=settings.facebook_client_secret,
        access_token_url="https://graph.facebook.com/v18.0/oauth/access_token",
        authorize_url="https://www.facebook.com/v18.0/dialog/oauth",
        api_base_url="https://graph.facebook.com/v18.0/",
        client_kwargs={"scope": "email public_profile"},
    )


def is_provider_configured(provider: str) -> bool:
    """True when the provider has credentials and was registered at startup."""
    return oauth.create_client(provider) is not None
