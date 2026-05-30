import pytest

from domain.entities.review import Review, ReviewPair
from domain.errors.domain_errors import ReviewAlreadySubmittedError
from domain.value_objects.rating import Rating


def review_from(reviewer: str, reviewee: str) -> Review:
    return Review(
        id=f"r-{reviewer}",
        task_id="t1",
        reviewer_id=reviewer,
        reviewee_id=reviewee,
        rating=Rating(5.0),
        comment="great",
    )


class TestReview:
    def test_starts_hidden(self):
        assert review_from("C", "H").is_revealed is False

    def test_is_from(self):
        r = review_from("C", "H")
        assert r.is_from("C")
        assert not r.is_from("H")


class TestBlindReveal:
    def test_first_submission_does_not_reveal(self):
        pair = ReviewPair(task_id="t1")
        revealed = pair.submit(review_from("C", "H"))
        assert revealed is False
        assert pair.client_review is not None
        assert pair.client_review.is_revealed is False

    def test_second_submission_reveals_both(self):
        pair = ReviewPair(task_id="t1")
        pair.submit(review_from("C", "H"))
        revealed = pair.submit(review_from("H", "C"))
        assert revealed is True
        assert pair.both_submitted()
        assert pair.client_review.is_revealed
        assert pair.hiver_review.is_revealed

    def test_duplicate_reviewer_rejected(self):
        pair = ReviewPair(task_id="t1")
        pair.submit(review_from("C", "H"))
        with pytest.raises(ReviewAlreadySubmittedError):
            pair.submit(review_from("C", "H"))
