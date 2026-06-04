import uuid
from datetime import datetime

from src.application.dtos.review_dtos import ReviewResponse, SubmitReviewRequest
from src.domain.entities.review import Review
from src.domain.entities.task import TaskStatus
from src.domain.errors.domain_errors import (
    ReviewAlreadySubmittedError,
    TaskNotCompletedError,
    TaskNotFoundError,
    UnauthorizedActionError,
)
from src.domain.interfaces.repositories import (
    IReviewRepository,
    ITaskRepository,
)
from src.domain.value_objects.rating import Rating


class SubmitReviewUseCase:
    """
    A party (client or hiver) submits a review of the counterparty.
    Constraints:
      - Task must be COMPLETED
      - Reviewer must be either the client or the assigned hiver
      - Each reviewer may submit only one review per task
    The blind-reveal DB trigger flips `is_revealed` on both rows once the
    counterparty review lands.
    """

    def __init__(
        self,
        task_repo: ITaskRepository,
        review_repo: IReviewRepository,
    ) -> None:
        self._task_repo = task_repo
        self._review_repo = review_repo

    async def execute(
        self, task_id: str, reviewer_id: str, body: SubmitReviewRequest
    ) -> ReviewResponse:
        task = await self._task_repo.find_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        if task.status != TaskStatus.COMPLETED:
            raise TaskNotCompletedError(task_id)

        if reviewer_id == task.client_id:
            reviewee_id = task.hiver_id
        elif reviewer_id == task.hiver_id:
            reviewee_id = task.client_id
        else:
            raise UnauthorizedActionError("submit a review for this task")

        if reviewee_id is None:
            raise UnauthorizedActionError("submit a review for an unassigned task")

        existing = await self._review_repo.find_by_task_and_reviewer(
            task_id=task_id, reviewer_id=reviewer_id
        )
        if existing is not None:
            raise ReviewAlreadySubmittedError(reviewer_id, task_id)

        review = Review(
            id=str(uuid.uuid4()),
            task_id=task_id,
            reviewer_id=reviewer_id,
            reviewee_id=reviewee_id,
            rating=Rating(body.rating),
            comment=body.comment,
            is_revealed=False,
            created_at=datetime.utcnow(),
        )
        saved = await self._review_repo.save(review)
        return ReviewResponse(
            id=saved.id,
            task_id=saved.task_id,
            reviewer_id=saved.reviewer_id,
            reviewee_id=saved.reviewee_id,
            rating=float(saved.rating.value),
            comment=saved.comment,
            is_revealed=saved.is_revealed,
            created_at=saved.created_at,
        )
