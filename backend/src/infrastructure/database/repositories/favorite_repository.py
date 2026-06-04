from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.favorite import Favorite
from src.domain.interfaces.repositories import IFavoriteRepository
from src.infrastructure.database.models import FavoriteModel


def _to_domain(m: FavoriteModel) -> Favorite:
    return Favorite(
        id=m.id,
        user_id=m.user_id,
        target_type=m.target_type,
        target_id=m.target_id,
        created_at=m.created_at,
    )


class PostgresFavoriteRepository(IFavoriteRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, favorite: Favorite) -> Favorite:
        # Idempotent: saving an already-saved item is a no-op, not a 500 on the
        # unique constraint. ON CONFLICT DO NOTHING keeps the existing row.
        stmt = (
            insert(FavoriteModel)
            .values(
                id=favorite.id or str(uuid.uuid4()),
                user_id=favorite.user_id,
                target_type=favorite.target_type,
                target_id=favorite.target_id,
            )
            .on_conflict_do_nothing(
                index_elements=["user_id", "target_type", "target_id"]
            )
        )
        await self._session.execute(stmt)
        await self._session.flush()
        existing = await self._session.execute(
            select(FavoriteModel).where(
                FavoriteModel.user_id == favorite.user_id,
                FavoriteModel.target_type == favorite.target_type,
                FavoriteModel.target_id == favorite.target_id,
            )
        )
        return _to_domain(existing.scalar_one())

    async def remove(self, user_id: str, target_type: str, target_id: str) -> None:
        await self._session.execute(
            delete(FavoriteModel).where(
                FavoriteModel.user_id == user_id,
                FavoriteModel.target_type == target_type,
                FavoriteModel.target_id == target_id,
            )
        )
        await self._session.flush()

    async def list_for_user(self, user_id: str, target_type: str) -> list[Favorite]:
        result = await self._session.execute(
            select(FavoriteModel)
            .where(
                FavoriteModel.user_id == user_id,
                FavoriteModel.target_type == target_type,
            )
            .order_by(FavoriteModel.created_at.desc())
        )
        return [_to_domain(m) for m in result.scalars()]

    async def target_ids(self, user_id: str, target_type: str) -> list[str]:
        result = await self._session.execute(
            select(FavoriteModel.target_id).where(
                FavoriteModel.user_id == user_id,
                FavoriteModel.target_type == target_type,
            )
        )
        return [row[0] for row in result]
