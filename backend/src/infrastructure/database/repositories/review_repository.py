from __future__ import annotations
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domain.entities.review import Review
from src.domain.value_objects.rating import Rating
from src.domain.interfaces.repositories import IReviewRepository
from src.infrastructure.database.models import ReviewModel


def _model_to_domain(m: ReviewModel) -> Review:
    return Review(
        id=m.id,
        task_id=m.task_id,
        reviewer_id=m.reviewer_id,
        reviewee_id=m.reviewee_id,
        rating=Rating(float(m.rating)),
        comment=m.comment,
        is_revealed=m.is_revealed,
        created_at=m.created_at,
    )


class PostgresReviewRepository(IReviewRepository):
    """
    Concrete review repository.
    NOTE: the blind-reveal pattern is enforced by a DB trigger (migration 010),
          so this repo simply persists each review — the trigger flips
          `is_revealed=true` on both rows once the second review lands.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, entity_id: str) -> Review | None:
        model = await self._session.get(ReviewModel, entity_id)
        return _model_to_domain(model) if model else None

    async def find_by_task(self, task_id: str) -> list[Review]:
        result = await self._session.execute(
            select(ReviewModel).where(ReviewModel.task_id == task_id)
            .order_by(ReviewModel.created_at.asc())
        )
        return [_model_to_domain(m) for m in result.scalars()]

    async def find_by_reviewee(self, reviewee_id: str) -> list[Review]:
        result = await self._session.execute(
            select(ReviewModel).where(ReviewModel.reviewee_id == reviewee_id)
            .where(ReviewModel.is_revealed.is_(True))
            .order_by(ReviewModel.created_at.desc())
        )
        return [_model_to_domain(m) for m in result.scalars()]

    async def find_by_task_and_reviewer(
        self, task_id: str, reviewer_id: str
    ) -> Review | None:
        result = await self._session.execute(
            select(ReviewModel)
            .where(ReviewModel.task_id == task_id)
            .where(ReviewModel.reviewer_id == reviewer_id)
        )
        model = result.scalar_one_or_none()
        return _model_to_domain(model) if model else None

    async def save(self, entity: Review) -> Review:
        model = await self._session.get(ReviewModel, entity.id)
        if model is None:
            model = ReviewModel(
                id=entity.id or str(uuid.uuid4()),
                task_id=entity.task_id,
                reviewer_id=entity.reviewer_id,
                reviewee_id=entity.reviewee_id,
                rating=float(entity.rating.value),
                comment=entity.comment,
                is_revealed=entity.is_revealed,
            )
            self._session.add(model)
        else:
            model.is_revealed = entity.is_revealed
        await self._session.flush()
        return entity

    async def delete(self, entity_id: str) -> None:
        model = await self._session.get(ReviewModel, entity_id)
        if model:
            await self._session.delete(model)
