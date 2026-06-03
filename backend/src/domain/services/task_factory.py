from __future__ import annotations

import uuid
from dataclasses import dataclass

from domain.entities.task import VALID_VERTICALS, Task
from domain.errors.domain_errors import InvalidVerticalError
from domain.value_objects.location import Location
from domain.value_objects.money import Money


@dataclass
class TaskCreateData:
    """Input DTO for task creation — validated by Pydantic in the API layer."""
    client_id: str
    vertical: str
    subcategory: str
    title: str
    description: str
    smart_answers: dict
    is_urgent: bool = False
    budget_min: float | None = None
    budget_max: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    location_display: str | None = None
    image_urls: list[str] | None = None


class TaskBuilder:
    """Abstract base for vertical-specific task builders."""

    def __init__(self, data: TaskCreateData) -> None:
        self.data = data

    def build(self) -> Task:
        self._validate()
        return Task(
            id=str(uuid.uuid4()),
            client_id=self.data.client_id,
            vertical=self.data.vertical,
            subcategory=self.data.subcategory,
            title=self.data.title,
            description=self.data.description,
            budget_min=Money.of(self.data.budget_min) if self.data.budget_min else None,
            budget_max=Money.of(self.data.budget_max) if self.data.budget_max else None,
            is_urgent=self.data.is_urgent,
            location=Location(
                self.data.latitude,
                self.data.longitude,
                self.data.location_display,
            ) if self.data.latitude and self.data.longitude else None,
            smart_answers=self.data.smart_answers,
            image_urls=self.data.image_urls or [],
        )

    def _validate(self) -> None:
        """Override in subclasses to add vertical-specific validation."""


class HomeTaskBuilder(TaskBuilder):
    """Home tasks — accepts optional smart_answers: property_type, size_sqm."""


class LearnTaskBuilder(TaskBuilder):
    """Learn tasks — accepts optional smart_answers: subject, student_age."""


class TechTaskBuilder(TaskBuilder):
    """Tech tasks — accepts optional smart_answers: device_type."""


class GenericTaskBuilder(TaskBuilder):
    """Fallback — no extra validation beyond base."""


_BUILDERS: dict[str, type[TaskBuilder]] = {
    "home":   HomeTaskBuilder,
    "learn":  LearnTaskBuilder,
    "tech":   TechTaskBuilder,
    "care":   GenericTaskBuilder,
    "move":   GenericTaskBuilder,
    "events": GenericTaskBuilder,
}


class TaskFactory:
    """
    Factory Pattern: creates Task with correct validation per vertical.
    OOP: Encapsulates construction complexity.

    Why: Each vertical has different required smart_answer fields.
    Without Factory: scattered if/elif blocks across the codebase.
    """

    @classmethod
    def create(cls, data: TaskCreateData) -> Task:
        if data.vertical not in VALID_VERTICALS:
            raise InvalidVerticalError(data.vertical)
        builder_class = _BUILDERS.get(data.vertical, GenericTaskBuilder)
        return builder_class(data).build()
