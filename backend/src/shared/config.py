from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Redis
    redis_url: str

    # Auth
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 30
    jwt_refresh_expire_days: int = 7

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
    cors_origins: List[str] = ["http://localhost:5173"]


settings = Settings()
