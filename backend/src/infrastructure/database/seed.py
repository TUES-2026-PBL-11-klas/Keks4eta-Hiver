"""
Seed script — populates the database with realistic dev data.
Run: python -m src.infrastructure.database.seed

Creates:
  - 2 clients (alice, bob)
  - 3 hivers (maria, stefan, ivan) with different levels
  - skills per vertical
  - 3 open tasks
"""
import asyncio
import uuid
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.shared.config import settings
from src.infrastructure.database.models import (
    UserModel, ClientModel, HiverModel, SkillModel,
    TaskModel, Base,
)

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def seed() -> None:
    engine = create_async_engine(settings.database_url, echo=False)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        async with session.begin():
            # ── Skills ──────────────────────────────────────────────────
            skills_data = [
                ("Cleaning",       "home"),  ("Plumbing",   "home"),
                ("Math tutoring",  "learn"), ("English",    "learn"),
                ("PC repair",      "tech"),  ("Phone repair","tech"),
                ("Moving help",    "move"),  ("Gardening",  "home"),
            ]
            skills = {name: SkillModel(id=str(uuid.uuid4()), name=name, vertical=v)
                      for name, v in skills_data}
            session.add_all(skills.values())

            # ── Clients ─────────────────────────────────────────────────
            alice_user = UserModel(
                id=str(uuid.uuid4()), email="alice@example.com",
                password_hash=pwd.hash("password123"),
                full_name="Alice Petrova", role="client",
            )
            alice_client = ClientModel(user_id=alice_user.id, rating_as_client=4.8, total_tasks=5)

            bob_user = UserModel(
                id=str(uuid.uuid4()), email="bob@example.com",
                password_hash=pwd.hash("password123"),
                full_name="Bob Ivanov", role="client",
            )
            bob_client = ClientModel(user_id=bob_user.id, rating_as_client=4.2, total_tasks=2)

            session.add_all([alice_user, alice_client, bob_user, bob_client])

            # ── Hivers ──────────────────────────────────────────────────
            maria_user = UserModel(
                id=str(uuid.uuid4()), email="maria@example.com",
                password_hash=pwd.hash("password123"),
                full_name="Maria Dimitrova", role="hiver",
            )
            maria_hiver = HiverModel(
                user_id=maria_user.id, bio="Expert cleaner, 5 years experience.",
                xp_points=600, level="master", avg_rating=4.9,
                completed_tasks=45, is_available_now=True, work_radius_km=10,
            )
            maria_hiver.skills = [skills["Cleaning"], skills["Gardening"]]

            stefan_user = UserModel(
                id=str(uuid.uuid4()), email="stefan@example.com",
                password_hash=pwd.hash("password123"),
                full_name="Stefan Georgiev", role="hiver",
            )
            stefan_hiver = HiverModel(
                user_id=stefan_user.id, bio="Math & physics tutor, university grad.",
                xp_points=120, level="experienced", avg_rating=4.7,
                completed_tasks=12, is_available_now=True, work_radius_km=5,
            )
            stefan_hiver.skills = [skills["Math tutoring"], skills["English"]]

            ivan_user = UserModel(
                id=str(uuid.uuid4()), email="ivan@example.com",
                password_hash=pwd.hash("password123"),
                full_name="Ivan Stoyanov", role="hiver",
            )
            ivan_hiver = HiverModel(
                user_id=ivan_user.id, bio="PC and phone repairs, fast turnaround.",
                xp_points=40, level="beginner", avg_rating=4.5,
                completed_tasks=4, is_available_now=False, work_radius_km=5,
            )
            ivan_hiver.skills = [skills["PC repair"], skills["Phone repair"]]

            session.add_all([
                maria_user, maria_hiver,
                stefan_user, stefan_hiver,
                ivan_user, ivan_hiver,
            ])

            # ── Tasks ────────────────────────────────────────────────────
            tasks = [
                TaskModel(
                    id=str(uuid.uuid4()), client_id=alice_client.user_id,
                    vertical="home", subcategory="cleaning",
                    title="Deep clean 2-bedroom apartment",
                    description="Need full deep clean before moving in. ~80sqm.",
                    budget_min=60, budget_max=100,
                    smart_answers={"property_type": "apartment", "size_sqm": 80},
                ),
                TaskModel(
                    id=str(uuid.uuid4()), client_id=alice_client.user_id,
                    vertical="learn", subcategory="math",
                    title="Math help for my 10-year-old",
                    description="Fractions and basic algebra. 1h/week.",
                    budget_min=20, budget_max=35, is_urgent=False,
                    smart_answers={"subject": "math", "student_age": 10},
                ),
                TaskModel(
                    id=str(uuid.uuid4()), client_id=bob_client.user_id,
                    vertical="tech", subcategory="pc_repair",
                    title="Laptop won't turn on",
                    description="Acer laptop, no display, charging LED works.",
                    budget_min=30, budget_max=80, is_urgent=True,
                    smart_answers={"device_type": "laptop", "brand": "Acer"},
                ),
            ]
            session.add_all(tasks)

    await engine.dispose()
    print("Seed complete.")
    print("  Clients : alice@example.com, bob@example.com  (password: password123)")
    print("  Hivers  : maria@example.com, stefan@example.com, ivan@example.com  (password: password123)")
    print("  Tasks   : 3 open tasks ready for offers")


if __name__ == "__main__":
    asyncio.run(seed())
