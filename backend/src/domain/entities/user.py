from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from domain.errors.domain_errors import InsufficientRatingError, InvalidEmailError
from domain.value_objects.location import Location
from domain.value_objects.money import Money
from domain.value_objects.rating import Rating
from domain.value_objects.work_radius import WorkRadius


@dataclass
class User(ABC):
    """
    Abstract base class for all user types.
    Never instantiated directly — always Client or Hiver.

    OOP: Abstraction + Encapsulation
    Encapsulates common user behavior; subclasses expose only
    what is relevant to their role.
    """
    id: str
    email: str
    _password_hash: str | None
    full_name: str
    phone: str | None = None
    avatar_url: str | None = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    # Social login: set when the account was created via Google/Facebook.
    # password_hash is None for OAuth-only accounts.
    oauth_provider: str | None = None   # "google" | "facebook" | None
    oauth_id: str | None = None         # the provider's stable user id ("sub")

    def __post_init__(self) -> None:
        self._validate_email(self.email)

    @abstractmethod
    def get_role(self) -> str:
        """Polymorphism: each subclass returns its own role string."""
        ...

    @abstractmethod
    def calculate_commission(self, amount: Money) -> Money:
        """
        Polymorphism: commission calculation differs by role and level.
        Client pays service fee; Hiver pays platform commission.
        Liskov: any User subtype works wherever User is expected.
        """
        ...

    def verify_password(self, plain: str) -> bool:
        """Encapsulated: password logic stays inside User.

        OAuth-only accounts have no password hash — they can never be
        authenticated with a password and must use social login.
        """
        if self._password_hash is None:
            return False
        from passlib.context import CryptContext
        return CryptContext(schemes=["bcrypt"], deprecated="auto").verify(plain, self._password_hash)

    def _validate_email(self, email: str) -> None:
        """Protected helper — shared by all subclasses."""
        parts = email.split("@")
        if len(parts) != 2 or "." not in parts[1]:
            raise InvalidEmailError(email)

    def deactivate(self) -> None:
        self.is_active = False

    @property
    def password_hash(self) -> str | None:
        return self._password_hash


@dataclass
class Client(User):
    """
    OOP: Inheritance from User.
    Client-specific behavior: posting tasks, rating hivers, favourites.
    """
    rating_as_client: Rating = field(default_factory=lambda: Rating(5.0))
    total_tasks: int = 0
    review_count: int = 0

    def get_role(self) -> str:
        return "client"

    def calculate_commission(self, amount: Money) -> Money:
        """Clients pay a flat 7% service fee."""
        return amount * 0.07

    def can_post_task(self) -> bool:
        """Business rule: clients with rating < 2.0 are restricted."""
        return self.rating_as_client.is_acceptable()

    def assert_can_post_task(self) -> None:
        if not self.can_post_task():
            raise InsufficientRatingError(self.rating_as_client.value)

    def record_task_posted(self) -> None:
        self.total_tasks += 1

    def update_rating(self, new_score: float) -> None:
        """Recalculates rolling average after a new review."""
        self.rating_as_client = self.rating_as_client.recalculate(self.review_count, new_score)
        self.review_count += 1


@dataclass
class Hiver(User):
    """
    OOP: Inheritance from User.
    Hiver-specific behavior: accepting tasks, earning, leveling up.
    """
    bio: str = ""
    xp_points: int = 0
    level: str = "beginner"   # beginner | experienced | master | legend
    avg_rating: Rating = field(default_factory=Rating.default)
    completed_tasks: int = 0
    review_count: int = 0
    is_available_now: bool = False
    work_radius: WorkRadius = field(default_factory=WorkRadius.default)
    location: Location | None = None
    skills: list[str] = field(default_factory=list)

    def get_role(self) -> str:
        return "hiver"

    def calculate_commission(self, amount: Money) -> Money:
        """
        Polymorphism: Hiver commission depends on level.
        Higher level = lower commission (gamification incentive).
        """
        rates: dict[str, float] = {
            "beginner":    0.20,
            "experienced": 0.18,
            "master":      0.16,
            "legend":      0.14,
        }
        return amount * rates[self.level]

    def add_xp(self, points: int) -> None:
        """Encapsulation: level-up logic is internal to Hiver."""
        self.xp_points += points
        self._recalculate_level()

    def _recalculate_level(self) -> None:
        thresholds = [("legend", 1500), ("master", 500), ("experienced", 100)]
        for level, threshold in thresholds:
            if self.xp_points >= threshold:
                self.level = level
                return
        self.level = "beginner"

    def update_rating(self, new_score: float) -> None:
        """Recalculates rolling average after a new review."""
        self.avg_rating = self.avg_rating.recalculate(self.review_count, new_score)
        self.review_count += 1
        self.completed_tasks += 1
        self.add_xp(10)

    def toggle_availability(self) -> None:
        self.is_available_now = not self.is_available_now

    def is_within_radius(self, task_location: Location) -> bool:
        if self.location is None:
            return False
        return self.work_radius.covers(self.location.distance_to_km(task_location))
