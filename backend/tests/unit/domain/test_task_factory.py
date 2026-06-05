import pytest

from src.domain.errors.domain_errors import InvalidVerticalError
from src.domain.services.task_factory import TaskCreateData, TaskFactory


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


class TestTaskFactory:
    @pytest.mark.parametrize(
        "vertical,field",
        [("home", "property_type"), ("learn", "subject"), ("tech", "device_type")],
    )
    def test_smart_answers_stored_when_provided(self, vertical, field):
        task = TaskFactory.create(
            make_data(vertical=vertical, smart_answers={field: "x"})
        )
        assert task.vertical == vertical
        assert task.smart_answers[field] == "x"

    @pytest.mark.parametrize(
        "vertical", ["home", "learn", "tech", "care", "move", "events"]
    )
    def test_smart_answers_optional(self, vertical):
        # Unified direction: smart_answers are optional — missing keys no longer
        # 500 or raise; the frontend collects them so tasks stay rich.
        task = TaskFactory.create(make_data(vertical=vertical, smart_answers={}))
        assert task.vertical == vertical

    def test_unknown_vertical_rejected(self):
        with pytest.raises(InvalidVerticalError):
            TaskFactory.create(make_data(vertical="spaceship"))
