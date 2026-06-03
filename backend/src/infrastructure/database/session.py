from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.shared.config import settings

# A shared, hosted Postgres (e.g. Supabase) is usually reached through a
# transaction-mode connection pooler (pgbouncer). In that mode asyncpg must NOT
# use prepared-statement caching, and the app should not layer its own pool on
# top of the server-side pool. For a direct/local connection we keep normal
# SQLAlchemy pooling for performance.
if settings.database_use_pooler:
    engine = create_async_engine(
        settings.database_url,
        echo=(settings.app_env == "development"),
        poolclass=NullPool,
        connect_args={"statement_cache_size": 0},
    )
else:
    engine = create_async_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        echo=(settings.app_env == "development"),
    )

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
