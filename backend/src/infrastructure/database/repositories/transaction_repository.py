from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.transaction import Transaction, TransactionStatus
from src.domain.interfaces.repositories import ITransactionRepository
from src.domain.value_objects.money import Money
from src.infrastructure.database.models import TransactionModel


def _model_to_domain(m: TransactionModel) -> Transaction:
    return Transaction(
        id=m.id,
        task_id=m.task_id,
        client_id=m.client_id,
        hiver_id=m.hiver_id,
        gross_amount=Money.of(m.gross_amount),
        platform_fee=Money.of(m.platform_fee),
        hiver_payout=Money.of(m.hiver_payout),
        stripe_payment_intent_id=m.stripe_payment_intent_id,
        status=TransactionStatus(m.status),
        released_at=m.released_at,
        refunded_at=m.refunded_at,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


class PostgresTransactionRepository(ITransactionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, entity_id: str) -> Transaction | None:
        model = await self._session.get(TransactionModel, entity_id)
        return _model_to_domain(model) if model else None

    async def find_by_task(self, task_id: str) -> Transaction | None:
        result = await self._session.execute(
            select(TransactionModel).where(TransactionModel.task_id == task_id)
        )
        model = result.scalar_one_or_none()
        return _model_to_domain(model) if model else None

    async def save(self, entity: Transaction) -> Transaction:
        model = await self._session.get(TransactionModel, entity.id)
        if model is None:
            model = TransactionModel(
                id=entity.id or str(uuid.uuid4()),
                task_id=entity.task_id,
                client_id=entity.client_id,
                hiver_id=entity.hiver_id,
                gross_amount=float(entity.gross_amount.value),
                platform_fee=float(entity.platform_fee.value),
                hiver_payout=float(entity.hiver_payout.value),
                stripe_payment_intent_id=entity.stripe_payment_intent_id,
                status=entity.status.value,
            )
            self._session.add(model)
        else:
            model.status = entity.status.value
            model.released_at = entity.released_at
            model.refunded_at = entity.refunded_at
            model.updated_at = entity.updated_at
        await self._session.flush()
        return entity

    async def find_by_hiver(self, hiver_id: str) -> list[Transaction]:
        result = await self._session.execute(
            select(TransactionModel)
            .where(TransactionModel.hiver_id == hiver_id)
            .order_by(TransactionModel.created_at.desc())
        )
        return [_model_to_domain(m) for m in result.scalars()]

    async def delete(self, entity_id: str) -> None:
        model = await self._session.get(TransactionModel, entity_id)
        if model:
            await self._session.delete(model)
