"""Unit tests for the Phase 5 favorites use cases."""

import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[3]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://t:t@localhost/t")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-at-least-32-chars-long!!")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_dummy")

from src.application.use_cases.favorites.favorite_use_cases import (
    AddFavoriteUseCase,
    ListFavoritesUseCase,
    RemoveFavoriteUseCase,
)
from src.domain.entities.favorite import Favorite
from src.domain.entities.task import Task
from src.domain.entities.user import Hiver
from src.domain.value_objects.rating import Rating
from src.domain.value_objects.work_radius import WorkRadius


class FakeFavoriteRepo:
    def __init__(self) -> None:
        self.items: list[Favorite] = []

    def _match(self, f: Favorite, user_id: str, tt: str, tid: str) -> bool:
        return f.user_id == user_id and f.target_type == tt and f.target_id == tid

    async def add(self, favorite: Favorite) -> Favorite:
        for f in self.items:
            if self._match(
                f, favorite.user_id, favorite.target_type, favorite.target_id
            ):
                return f  # idempotent
        self.items.append(favorite)
        return favorite

    async def remove(self, user_id: str, target_type: str, target_id: str) -> None:
        self.items = [
            f for f in self.items if not self._match(f, user_id, target_type, target_id)
        ]

    async def list_for_user(self, user_id: str, target_type: str) -> list[Favorite]:
        return [
            f
            for f in self.items
            if f.user_id == user_id and f.target_type == target_type
        ]

    async def target_ids(self, user_id: str, target_type: str) -> list[str]:
        return [f.target_id for f in await self.list_for_user(user_id, target_type)]


class FakeTaskRepo:
    def __init__(self, tasks: list[Task]) -> None:
        self.tasks = {t.id: t for t in tasks}

    async def find_by_id(self, task_id: str) -> Task | None:
        return self.tasks.get(task_id)


class FakeHiverRepo:
    def __init__(self, hivers: list[Hiver]) -> None:
        self.hivers = {h.id: h for h in hivers}

    async def find_by_id(self, hiver_id: str) -> Hiver | None:
        return self.hivers.get(hiver_id)


def make_task(tid: str) -> Task:
    return Task(
        id=tid,
        client_id="c1",
        vertical="home",
        subcategory="cleaning",
        title=f"Task {tid}",
        description="x",
    )


def make_hiver(hid: str) -> Hiver:
    return Hiver(
        id=hid,
        email=f"{hid}@t.com",
        _password_hash=None,
        full_name=f"Hiver {hid}",
        avg_rating=Rating(4.0),
        work_radius=WorkRadius(5),
    )


class TestAddRemoveFavorite:
    async def test_add_then_listed_in_ids(self):
        repo = FakeFavoriteRepo()
        await AddFavoriteUseCase(repo).execute("u1", "task", "t1")
        lister = ListFavoritesUseCase(repo, FakeTaskRepo([]), FakeHiverRepo([]))
        ids = await lister.ids("u1")
        assert ids.tasks == ["t1"]
        assert ids.hivers == []

    async def test_add_is_idempotent(self):
        repo = FakeFavoriteRepo()
        await AddFavoriteUseCase(repo).execute("u1", "task", "t1")
        await AddFavoriteUseCase(repo).execute("u1", "task", "t1")
        assert len(repo.items) == 1

    async def test_remove(self):
        repo = FakeFavoriteRepo()
        await AddFavoriteUseCase(repo).execute("u1", "hiver", "h1")
        await RemoveFavoriteUseCase(repo).execute("u1", "hiver", "h1")
        assert repo.items == []


class TestListFavorites:
    async def test_resolves_saved_tasks_skipping_deleted(self):
        repo = FakeFavoriteRepo()
        await AddFavoriteUseCase(repo).execute("u1", "task", "t1")
        await AddFavoriteUseCase(repo).execute("u1", "task", "gone")  # no longer exists
        lister = ListFavoritesUseCase(
            repo, FakeTaskRepo([make_task("t1")]), FakeHiverRepo([])
        )
        tasks = await lister.tasks("u1")
        assert [t.id for t in tasks] == ["t1"]

    async def test_resolves_saved_hivers(self):
        repo = FakeFavoriteRepo()
        await AddFavoriteUseCase(repo).execute("u1", "hiver", "h1")
        lister = ListFavoritesUseCase(
            repo, FakeTaskRepo([]), FakeHiverRepo([make_hiver("h1")])
        )
        hivers = await lister.hivers("u1")
        assert [h.user_id for h in hivers] == ["h1"]

    async def test_ids_split_by_type(self):
        repo = FakeFavoriteRepo()
        await AddFavoriteUseCase(repo).execute("u1", "task", "t1")
        await AddFavoriteUseCase(repo).execute("u1", "hiver", "h1")
        lister = ListFavoritesUseCase(repo, FakeTaskRepo([]), FakeHiverRepo([]))
        ids = await lister.ids("u1")
        assert set(ids.tasks) == {"t1"}
        assert set(ids.hivers) == {"h1"}
