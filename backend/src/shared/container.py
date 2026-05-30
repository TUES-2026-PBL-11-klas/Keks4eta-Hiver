"""
DI wiring — keeps router files free of import chains.
SOLID D: high-level modules depend on abstractions (interfaces),
         not on concrete Postgres classes.

Each factory is a plain function; FastAPI's Depends() resolves them
per-request, which gives us automatic scoping without a DI framework.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.repositories.user_repository import (
    PostgresClientRepository,
    PostgresHiverRepository,
)
from src.infrastructure.database.repositories.task_repository import PostgresTaskRepository
from src.infrastructure.database.repositories.offer_repository import PostgresOfferRepository
from src.infrastructure.database.repositories.transaction_repository import (
    PostgresTransactionRepository,
)

from src.application.use_cases.auth.register_use_case import RegisterUseCase
from src.application.use_cases.auth.login_use_case import LoginUseCase
from src.application.use_cases.tasks.create_task_use_case import CreateTaskUseCase
from src.application.use_cases.tasks.get_task_use_case import GetTaskUseCase
from src.application.use_cases.tasks.list_tasks_use_case import ListClientTasksUseCase
from src.application.use_cases.offers.create_offer_use_case import CreateOfferUseCase
from src.application.use_cases.offers.accept_offer_use_case import AcceptOfferUseCase
from src.application.use_cases.payments.release_escrow_use_case import ReleaseEscrowUseCase


def make_register_use_case(session: AsyncSession) -> RegisterUseCase:
    return RegisterUseCase(
        client_repo=PostgresClientRepository(session),
        hiver_repo=PostgresHiverRepository(session),
    )


def make_login_use_case(session: AsyncSession) -> LoginUseCase:
    return LoginUseCase(
        client_repo=PostgresClientRepository(session),
        hiver_repo=PostgresHiverRepository(session),
    )


def make_create_task_use_case(session: AsyncSession) -> CreateTaskUseCase:
    return CreateTaskUseCase(task_repo=PostgresTaskRepository(session))


def make_get_task_use_case(session: AsyncSession) -> GetTaskUseCase:
    return GetTaskUseCase(task_repo=PostgresTaskRepository(session))


def make_list_tasks_use_case(session: AsyncSession) -> ListClientTasksUseCase:
    return ListClientTasksUseCase(task_repo=PostgresTaskRepository(session))


def make_create_offer_use_case(session: AsyncSession) -> CreateOfferUseCase:
    return CreateOfferUseCase(
        task_repo=PostgresTaskRepository(session),
        offer_repo=PostgresOfferRepository(session),
        hiver_repo=PostgresHiverRepository(session),
    )


def make_accept_offer_use_case(session: AsyncSession) -> AcceptOfferUseCase:
    return AcceptOfferUseCase(
        task_repo=PostgresTaskRepository(session),
        offer_repo=PostgresOfferRepository(session),
    )


def make_release_escrow_use_case(session: AsyncSession) -> ReleaseEscrowUseCase:
    return ReleaseEscrowUseCase(
        task_repo=PostgresTaskRepository(session),
        transaction_repo=PostgresTransactionRepository(session),
    )
