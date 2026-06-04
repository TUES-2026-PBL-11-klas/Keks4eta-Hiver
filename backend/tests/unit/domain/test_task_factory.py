import pytest

from domain.errors.domain_errors import (
    InvalidVerticalError,
    MissingSmartAnswerError,
)
from domain.services.task_factory import TaskCreateData, TaskFactory


def make_data(**overrides) -> TaskCreateData:
    defaults = dict(
        client_id="c1",
        vertical="care",
        subcategory="dog walking",
        title="Walk my dog",
        description="Twice a day",
        smart_answers={},
    )
    defaults.update(overrides)
    return TaskCreateData(**defaults)


class TestSmartAnswerValidation:
    """The missing-smart-answer case is exactly what used to 500 on POST /tasks."""

    @pytest.mark.parametrize(
        "vertical,field",
        [("home", "property_type"), ("learn", "subject"), ("tech", "device_type")],
    )
    def test_missing_required_answer_rejected(self, vertical, field):
        with pytest.raises(MissingSmartAnswerError):
            TaskFactory.create(make_data(vertical=vertical, smart_answers={}))

    @pytest.mark.parametrize(
        "vertical,field",
        [("home", "property_type"), ("learn", "subject"), ("tech", "device_type")],
    )
    def test_with_required_answer_succeeds(self, vertical, field):
        task = TaskFactory.create(
            make_data(vertical=vertical, smart_answers={field: "x"})
        )
        assert task.vertical == vertical
        assert task.smart_answers[field] == "x"

    def test_generic_vertical_needs_no_smart_answers(self):
        task = TaskFactory.create(make_data(vertical="care", smart_answers={}))
        assert task.vertical == "care"

    def test_unknown_vertical_rejected(self):
        with pytest.raises(InvalidVerticalError):
            TaskFactory.create(make_data(vertical="spaceship"))
