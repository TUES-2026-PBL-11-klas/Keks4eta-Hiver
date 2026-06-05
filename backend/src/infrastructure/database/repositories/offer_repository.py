from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.offer import Offer, OfferStatus
from src.domain.interfaces.repositories import IOfferRepository
from src.domain.value_objects.money import Money
from src.infrastructure.database.models import OfferModel


def _model_to_domain(m: OfferModel) -> Offer:
    return Offer(
        id=m.id,
        task_id=m.task_id,
        hiver_id=m.hiver_id,
        price=Money.of(m.price),
        message=m.message,
        estimated_hours=float(m.estimated_hours),
        status=OfferStatus(m.status),
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class PostgresOfferRepository(IOfferRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, entity_id: str) -> Offer | None:
        model = await self._session.get(OfferModel, entity_id)
        return _model_to_domain(model) if model else None

    async def find_by_task(self, task_id: str) -> list[Offer]:
        result = await self._session.execute(
            select(OfferModel).where(OfferModel.task_id == task_id)
            .order_by(OfferModel.created_at.asc())
        )
        return [_model_to_domain(m) for m in result.scalars()]

    async def find_by_hiver(self, hiver_id: str) -> list[Offer]:
        result = await self._session.execute(
            select(OfferModel).where(OfferModel.hiver_id == hiver_id)
            .order_by(OfferModel.created_at.desc())
        )
        return [_model_to_domain(m) for m in result.scalars()]

    async def find_by_task_and_hiver(self, task_id: str, hiver_id: str) -> Offer | None:
        result = await self._session.execute(
            select(OfferModel)
            .where(OfferModel.task_id == task_id, OfferModel.hiver_id == hiver_id)
        )
        model = result.scalar_one_or_none()
        return _model_to_domain(model) if model else None

    async def save(self, entity: Offer) -> Offer:
        model = await self._session.get(OfferModel, entity.id)
        if model is None:
            model = OfferModel(
                id=entity.id or str(uuid.uuid4()),
                task_id=entity.task_id,
                hiver_id=entity.hiver_id,
                price=float(entity.price.value),
                message=entity.message,
                estimated_hours=entity.estimated_hours,
                status=entity.status.value,
            )
            self._session.add(model)
        else:
            model.status = entity.status.value
            model.updated_at = entity.updated_at
        await self._session.flush()
        return entity

    async def delete(self, entity_id: str) -> None:
        model = await self._session.get(OfferModel, entity_id)
        if model:
            await self._session.delete(model)
