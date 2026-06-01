from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    # Look for .env in the current dir (repo root) AND one level up — so the
    # backend works whether you run it from the repo root or from backend/.
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), extra="ignore")

    # Database
    database_url: str
    database_pool_size: int = 10
    database_max_overflow: int = 20
    # Set true when DATABASE_URL points at a transaction-mode connection pooler
    # (e.g. Supabase's pgbouncer on port 6543). Disables app-side pooling and
    # asyncpg prepared-statement caching, which pgbouncer transaction mode breaks.
    database_use_pooler: bool = False

    # Redis
    redis_url: str

    # Auth
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 30
    jwt_refresh_expire_days: int = 7

    # Social login (OAuth 2.0 / OpenID Connect). Leave blank to disable a provider.
    google_client_id: str = ""
    google_client_secret: str = ""
    facebook_client_id: str = ""
    facebook_client_secret: str = ""
    # Where the OAuth provider sends the user back (must match the provider console).
    # The provider name is appended: {oauth_redirect_base_url}/auth/oauth/{provider}/callback
    oauth_redirect_base_url: str = "http://localhost:8000"
    # SPA route the backend redirects to after a successful OAuth login, carrying tokens.
    frontend_url: str = "http://localhost:5173"

    # Stripe
    stripe_secret_key: str
    stripe_webhook_secret: str

    # External services
    google_maps_api_key: str = ""
    supabase_url: str = ""
    supabase_service_key: str = ""
    firebase_credentials_json: str = ""

    # App
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "DEBUG"
    # Stored as a raw string so pydantic-settings doesn't try to JSON-parse it
    # from .env. Use `cors_origins_list` to get the parsed list.
    cors_origins: str = "http://localhost:5173"
    # All feature routers are mounted under this prefix (the SPA calls /api/v1/...).
    api_prefix: str = "/api/v1"

    @property
    def cors_origins_list(self) -> List[str]:
        """Comma-separated CORS origins from .env, parsed into a list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
