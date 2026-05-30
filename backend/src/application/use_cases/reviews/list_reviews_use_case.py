from src.domain.interfaces.repositories import IReviewRepository
from src.application.dtos.review_dtos import ReviewResponse


class ListTaskReviewsUseCase:
    """Returns all reviews for a task. Caller may filter by `is_revealed`."""

    def __init__(self, review_repo: IReviewRepository) -> None:
        self._review_repo = review_repo

    async def execute(
        self, task_id: str, only_revealed: bool = False
    ) -> list[ReviewResponse]:
        reviews = await self._review_repo.find_by_task(task_id)
        if only_revealed:
            reviews = [r for r in reviews if r.is_revealed]
        return [
            ReviewResponse(
                id=r.id,
                task_id=r.task_id,
                reviewer_id=r.reviewer_id,
                reviewee_id=r.reviewee_id,
                rating=float(r.rating.value),
                comment=r.comment,
                is_revealed=r.is_revealed,
                created_at=r.created_at,
            )
            for r in reviews
        ]


class ListUserReviewsUseCase:
    """Returns all revealed reviews received by a given user."""

    def __init__(self, review_repo: IReviewRepository) -> None:
        self._review_repo = review_repo

    async def execute(self, user_id: str) -> list[ReviewResponse]:
        reviews = await self._review_repo.find_by_reviewee(user_id)
        return [
            ReviewResponse(
                id=r.id,
                task_id=r.task_id,
                reviewer_id=r.reviewer_id,
                reviewee_id=r.reviewee_id,
                rating=float(r.rating.value),
                comment=r.comment,
                is_revealed=r.is_revealed,
                created_at=r.created_at,
            )
            for r in reviews
        ]
