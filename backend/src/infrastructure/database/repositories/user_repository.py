from __future__ import annotations

import uuid

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import Client, Hiver
from src.domain.interfaces.repositories import (
    IClientRepository,
    IHiverRepository,
    PaginatedResult,
)
from src.domain.value_objects.rating import Rating
from src.domain.value_objects.work_radius import WorkRadius
from src.infrastructure.database.models import ClientModel, HiverModel, UserModel

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _client_model_to_domain(u: UserModel, c: ClientModel) -> Client:
    return Client(
        id=u.id,
        email=u.email,
        _password_hash=u.password_hash,
        full_name=u.full_name,
        phone=u.phone,
        avatar_url=u.avatar_url,
        is_active=u.is_active,
        oauth_provider=u.oauth_provider,
        oauth_id=u.oauth_id,
        rating_as_client=Rating(float(c.rating_as_client)),
        total_tasks=c.total_tasks,
        review_count=c.review_count,
    )


def _hiver_model_to_domain(u: UserModel, h: HiverModel) -> Hiver:
    return Hiver(
        id=u.id,
        email=u.email,
        _password_hash=u.password_hash,
        full_name=u.full_name,
        phone=u.phone,
        avatar_url=u.avatar_url,
        is_active=u.is_active,
        oauth_provider=u.oauth_provider,
        oauth_id=u.oauth_id,
        bio=h.bio,
        xp_points=h.xp_points,
        level=h.level,
        avg_rating=Rating(float(h.avg_rating)),
        completed_tasks=h.completed_tasks,
        review_count=h.review_count,
        is_available_now=h.is_available_now,
        work_radius=WorkRadius(h.work_radius_km),
        skills=[s.name for s in h.skills],
    )


class PostgresClientRepository(IClientRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, entity_id: str) -> Client | None:
        result = await self._session.execute(
            select(UserModel, ClientModel)
            .join(ClientModel, UserModel.id == ClientModel.user_id)
            .where(UserModel.id == entity_id)
        )
        row = result.first()
        if not row:
            return None
        return _client_model_to_domain(row.UserModel, row.ClientModel)

    async def find_by_email(self, email: str) -> Client | None:
        result = await self._session.execute(
            select(UserModel, ClientModel)
            .join(ClientModel, UserModel.id == ClientModel.user_id)
            .where(UserModel.email == email)
        )
        row = result.first()
        if not row:
            return None
        return _client_model_to_domain(row.UserModel, row.ClientModel)

    async def find_by_oauth(self, provider: str, oauth_id: str) -> Client | None:
        result = await self._session.execute(
            select(UserModel, ClientModel)
            .join(ClientModel, UserModel.id == ClientModel.user_id)
            .where(UserModel.oauth_provider == provider, UserModel.oauth_id == oauth_id)
        )
        row = result.first()
        if not row:
            return None
        return _client_model_to_domain(row.UserModel, row.ClientModel)

    async def save(self, entity: Client) -> Client:
        user = await self._session.get(UserModel, entity.id)
        if user is None:
            user = UserModel(
                id=entity.id or str(uuid.uuid4()),
                email=entity.email,
                password_hash=entity.password_hash,
                full_name=entity.full_name,
                phone=entity.phone,
                avatar_url=entity.avatar_url,
                role="client",
                is_active=entity.is_active,
                oauth_provider=entity.oauth_provider,
                oauth_id=entity.oauth_id,
            )
            client = ClientModel(
                user_id=user.id,
                rating_as_client=entity.rating_as_client.value,
                total_tasks=entity.total_tasks,
                review_count=entity.review_count,
            )
            self._session.add(user)
            self._session.add(client)
        else:
            user.email = entity.email
            user.full_name = entity.full_name
            user.phone = entity.phone
            user.avatar_url = entity.avatar_url
            user.is_active = entity.is_active
            client = await self._session.get(ClientModel, entity.id)
            if client:
                client.rating_as_client = entity.rating_as_client.value
                client.total_tasks = entity.total_tasks
                client.review_count = entity.review_count
        await self._session.flush()
        return entity

    async def find_all(self, page: int = 1, page_size: int = 20) -> PaginatedResult[Client]:
        result = await self._session.execute(
            select(UserModel, ClientModel)
            .join(ClientModel, UserModel.id == ClientModel.user_id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = result.all()
        items = [_client_model_to_domain(r.UserModel, r.ClientModel) for r in rows]
        return PaginatedResult(items=items, total=len(items), page=page, page_size=page_size)

    async def delete(self, entity_id: str) -> None:
        user = await self._session.get(UserModel, entity_id)
        if user:
            await self._session.delete(user)


class PostgresHiverRepository(IHiverRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, entity_id: str) -> Hiver | None:
        result = await self._session.execute(
            select(UserModel, HiverModel)
            .join(HiverModel, UserModel.id == HiverModel.user_id)
            .where(UserModel.id == entity_id)
        )
        row = result.first()
        if not row:
            return None
        return _hiver_model_to_domain(row.UserModel, row.HiverModel)

    async def find_by_email(self, email: str) -> Hiver | None:
        result = await self._session.execute(
            select(UserModel, HiverModel)
            .join(HiverModel, UserModel.id == HiverModel.user_id)
            .where(UserModel.email == email)
        )
        row = result.first()
        if not row:
            return None
        return _hiver_model_to_domain(row.UserModel, row.HiverModel)

    async def find_by_oauth(self, provider: str, oauth_id: str) -> Hiver | None:
        result = await self._session.execute(
            select(UserModel, HiverModel)
            .join(HiverModel, UserModel.id == HiverModel.user_id)
            .where(UserModel.oauth_provider == provider, UserModel.oauth_id == oauth_id)
        )
        row = result.first()
        if not row:
            return None
        return _hiver_model_to_domain(row.UserModel, row.HiverModel)

    async def save(self, entity: Hiver) -> Hiver:
        user = await self._session.get(UserModel, entity.id)
        if user is None:
            user = UserModel(
                id=entity.id or str(uuid.uuid4()),
                email=entity.email,
                password_hash=entity.password_hash,
                full_name=entity.full_name,
                phone=entity.phone,
                avatar_url=entity.avatar_url,
                role="hiver",
                is_active=entity.is_active,
                oauth_provider=entity.oauth_provider,
                oauth_id=entity.oauth_id,
            )
            hiver = HiverModel(
                user_id=user.id,
                bio=entity.bio,
                xp_points=entity.xp_points,
                level=entity.level,
                avg_rating=entity.avg_rating.value,
                completed_tasks=entity.completed_tasks,
                review_count=entity.review_count,
                is_available_now=entity.is_available_now,
                work_radius_km=entity.work_radius.km,
            )
            self._session.add(user)
            self._session.add(hiver)
        else:
            user.email = entity.email
            user.full_name = entity.full_name
            user.phone = entity.phone
            user.avatar_url = entity.avatar_url
            user.is_active = entity.is_active
            hiver = await self._session.get(HiverModel, entity.id)
            if hiver:
                hiver.bio = entity.bio
                hiver.xp_points = entity.xp_points
                hiver.level = entity.level
                hiver.avg_rating = entity.avg_rating.value
                hiver.completed_tasks = entity.completed_tasks
                hiver.is_available_now = entity.is_available_now
                hiver.work_radius_km = entity.work_radius.km
        await self._session.flush()
        return entity

    async def find_available_near(self, location, radius_km, vertical=None) -> list[Hiver]:
        # Uses the PL/pgSQL function from migration 014
        from sqlalchemy import text
        result = await self._session.execute(
            text("SELECT user_id FROM find_hivers_in_radius(:lat, :lng, :radius, :vertical)"),
            {"lat": location.latitude, "lng": location.longitude,
             "radius": radius_km, "vertical": vertical},
        )
        ids = [row.user_id for row in result]
        hivers = []
        for hiver_id in ids:
            h = await self.find_by_id(hiver_id)
            if h:
                hivers.append(h)
        return hivers

    async def find_all(self, page: int = 1, page_size: int = 20) -> PaginatedResult[Hiver]:
        result = await self._session.execute(
            select(UserModel, HiverModel)
            .join(HiverModel, UserModel.id == HiverModel.user_id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        rows = result.all()
        items = [_hiver_model_to_domain(r.UserModel, r.HiverModel) for r in rows]
        return PaginatedResult(items=items, total=len(items), page=page, page_size=page_size)

    async def delete(self, entity_id: str) -> None:
        user = await self._session.get(UserModel, entity_id)
        if user:
            await self._session.delete(user)
