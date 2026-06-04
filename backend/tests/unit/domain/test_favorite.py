import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[3]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

import pytest

from src.domain.entities.favorite import Favorite
from src.domain.errors.domain_errors import BusinessRuleViolationError


class TestFavorite:
    def test_valid_task_favorite(self):
        fav = Favorite(id="f1", user_id="u1", target_type="task", target_id="t1")
        assert fav.target_type == "task"

    def test_valid_hiver_favorite(self):
        fav = Favorite(id="f2", user_id="u1", target_type="hiver", target_id="h1")
        assert fav.target_type == "hiver"

    def test_invalid_target_type_rejected(self):
        with pytest.raises(BusinessRuleViolationError):
            Favorite(id="f3", user_id="u1", target_type="spaceship", target_id="x")
