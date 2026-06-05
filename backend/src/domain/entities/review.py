from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from src.domain.errors.domain_errors import ReviewAlreadySubmittedError
from src.domain.value_objects.rating import Rating


@dataclass
class Review:
    """
    Domain entity: a bidirectional review after task completion.

    Both parties submit reviews independently; neither sees the other's
    review until both have submitted (blind reveal pattern).

    OOP: Encapsulation — reveal logic is internal.
    """
    id: str
    task_id: str
    reviewer_id: str
    reviewee_id: str
    rating: Rating
    comment: str
    is_revealed: bool = False   # True once both parties have submitted
    created_at: datetime = field(default_factory=datetime.utcnow)

    def reveal(self) -> None:
        """Called by domain service once both reviews exist."""
        self.is_revealed = True

    def is_from(self, user_id: str) -> bool:
        return self.reviewer_id == user_id


@dataclass
class ReviewPair:
    """
    Domain service helper: manages the blind-reveal pattern for a task.

    OOP: Encapsulation — the pair knows when to reveal both reviews.
    """
    task_id: str
    client_review: Review | None = None
    hiver_review: Review | None = None

    def submit(self, review: Review) -> bool:
        """
        Submit a review. Returns True if both reviews are now present
        and triggers revelation.
        """
        if review.reviewer_id == self._expect_client_id() and self.client_review:
            raise ReviewAlreadySubmittedError(review.reviewer_id, self.task_id)
        if review.reviewer_id == self._expect_hiver_id() and self.hiver_review:
            raise ReviewAlreadySubmittedError(review.reviewer_id, self.task_id)

        if self.client_review is None and not (self.hiver_review and self.hiver_review.is_from(review.reviewer_id)):
            self.client_review = review
        else:
            self.hiver_review = review

        if self.both_submitted():
            self._reveal_both()
            return True
        return False

    def both_submitted(self) -> bool:
        return self.client_review is not None and self.hiver_review is not None

    def _reveal_both(self) -> None:
        if self.client_review:
            self.client_review.reveal()
        if self.hiver_review:
            self.hiver_review.reveal()

    def _expect_client_id(self) -> str | None:
        return self.client_review.reviewer_id if self.client_review else None

    def _expect_hiver_id(self) -> str | None:
        return self.hiver_review.reviewer_id if self.hiver_review else None
