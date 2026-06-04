from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from shared.logger import logger


@asynccontextmanager
async def db_transaction(session: AsyncSession) -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager — Python's equivalent of Java try-with-resources.
    Guarantees: transaction is always committed or rolled back.
    Usage: async with db_transaction(session): ...

    OOP: Encapsulates transaction lifecycle management.
    Any code using this never needs to write BEGIN/COMMIT/ROLLBACK.
    """
    try:
        yield session
        await session.commit()
        logger.info("transaction.committed")
    except Exception as e:
        await session.rollback()
        logger.error("transaction.rolled_back", error=str(e))
        raise
    finally:
        await session.close()  # always released — equivalent of try-with-resources
