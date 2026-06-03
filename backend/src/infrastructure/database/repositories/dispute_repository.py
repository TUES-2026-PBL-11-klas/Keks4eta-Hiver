from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.dispute import Dispute, DisputeStatus
from src.domain.interfaces.repositories import IDisputeRepository
from src.infrastructure.database.models import DisputeModel


def _to_domain(m: DisputeModel) -> Dispute:
    return Dispute(
        id=m.id,
        task_id=m.task_id,
        opened_by_id=m.opened_by_id,
        reason=m.reason,
        status=DisputeStatus(m.status),
        admin_note=m.admin_note,
        created_at=m.created_at,
        resolved_at=m.resolved_at,
    )


class PostgresDisputeRepository(IDisputeRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, dispute: Dispute) -> Dispute:
        model = DisputeModel(
            id=dispute.id or str(uuid.uuid4()),
            task_id=dispute.task_id,
            opened_by_id=dispute.opened_by_id,
            reason=dispute.reason,
            status=dispute.status.value,
            admin_note=dispute.admin_note,
        )
        self._session.add(model)
        await self._session.flush()
        return _to_domain(model)

    async def find_by_task(self, task_id: str) -> Dispute | None:
        result = await self._session.execute(
            select(DisputeModel).where(DisputeModel.task_id == task_id)
        )
        model = result.scalar_one_or_none()
        return _to_domain(model) if model else None

    async def save(self, dispute: Dispute) -> Dispute:
        model = await self._session.get(DisputeModel, dispute.id)
        if model is None:
            return await self.add(dispute)
        model.status = dispute.status.value
        model.admin_note = dispute.admin_note
        model.resolved_at = dispute.resolved_at
        await self._session.flush()
        return dispute
