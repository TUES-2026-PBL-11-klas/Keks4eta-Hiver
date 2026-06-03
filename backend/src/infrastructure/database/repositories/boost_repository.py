from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.boost import Boost
from src.domain.interfaces.repositories import IBoostRepository
from src.infrastructure.database.models import BoostModel


def _to_domain(m: BoostModel) -> Boost:
    return Boost(
        id=m.id,
        hiver_id=m.hiver_id,
        expires_at=m.expires_at,
        stripe_payment_id=m.stripe_payment_id,
        vertical=m.vertical,
        created_at=m.created_at,
    )


class PostgresBoostRepository(IBoostRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, boost: Boost) -> Boost:
        model = BoostModel(
            id=boost.id or str(uuid.uuid4()),
            hiver_id=boost.hiver_id,
            vertical=boost.vertical,
            expires_at=boost.expires_at,
            stripe_payment_id=boost.stripe_payment_id,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_domain(model)

    async def find_active_for_hiver(self, hiver_id: str) -> Boost | None:
        result = await self._session.execute(
            select(BoostModel)
            .where(BoostModel.hiver_id == hiver_id, BoostModel.expires_at > func.now())
            .order_by(BoostModel.expires_at.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return _to_domain(model) if model else None

    async def active_hiver_ids(self, vertical: str | None = None) -> set[str]:
        # Active = not expired. A global boost (vertical NULL) applies to any
        # search; a vertical-scoped boost applies only to that vertical.
        stmt = select(BoostModel.hiver_id).where(BoostModel.expires_at > func.now())
        if vertical is not None:
            stmt = stmt.where(
                or_(BoostModel.vertical.is_(None), BoostModel.vertical == vertical)
            )
        result = await self._session.execute(stmt)
        return {row[0] for row in result}
