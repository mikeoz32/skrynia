from __future__ import annotations

import os
from collections.abc import AsyncGenerator, Awaitable, Callable, Mapping
from importlib import import_module
from typing import Any, cast

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)

from .model import Base

ModelMapping = Mapping[str, Any]
MigrationCallback = Callable[[AsyncConnection], Awaitable[None]]


def _env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _run_alembic_upgrade(
    sync_connection: Connection,
    alembic_config_path: str,
    migration_target: str,
) -> None:
    try:
        command_module = cast(Any, import_module("alembic.command"))
        config_module = cast(Any, import_module("alembic.config"))
    except ModuleNotFoundError as error:
        raise RuntimeError(
            "Alembic is required for migration mode. Install `alembic` or "
            "override sqla_migration_callback."
        ) from error

    config = config_module.Config(alembic_config_path)
    config.attributes["connection"] = sync_connection
    command_module.upgrade(config, migration_target)


async def _initialize_schema(
    connection: AsyncConnection,
    *,
    use_migrations: bool,
    migration_callback: MigrationCallback | None,
    alembic_config_path: str | None,
    migration_target: str,
) -> None:
    if not use_migrations:
        await connection.run_sync(Base.metadata.create_all)
        return

    if migration_callback is not None:
        await migration_callback(connection)
        return

    if alembic_config_path is None:
        raise RuntimeError(
            "Migration mode is enabled but no Alembic config path is set. "
            "Set SKRY_SQLA_ALEMBIC_CONFIG or override sqla_migration_callback."
        )

    await connection.run_sync(
        lambda sync_connection: _run_alembic_upgrade(
            sync_connection=sync_connection,
            alembic_config_path=alembic_config_path,
            migration_target=migration_target,
        )
    )


@pytest.fixture(scope="session")
def sqla_test_database_uri() -> str:
    return os.getenv("SKRY_SQLA_TEST_DATABASE_URI", "sqlite+aiosqlite:///:memory:")


@pytest.fixture(scope="session")
def sqla_use_migrations() -> bool:
    return _env_flag("SKRY_SQLA_USE_MIGRATIONS", default=False)


@pytest.fixture(scope="session")
def sqla_alembic_config_path() -> str | None:
    return os.getenv("SKRY_SQLA_ALEMBIC_CONFIG")


@pytest.fixture(scope="session")
def sqla_migration_target() -> str:
    return os.getenv("SKRY_SQLA_MIGRATION_TARGET", "head")


@pytest.fixture(scope="session")
def sqla_migration_callback() -> MigrationCallback | None:
    return None


@pytest_asyncio.fixture(scope="session")
async def sqla_main_engine(
    sqla_test_database_uri: str,
    sqla_use_migrations: bool,
    sqla_migration_callback: MigrationCallback | None,
    sqla_alembic_config_path: str | None,
    sqla_migration_target: str,
) -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(sqla_test_database_uri)

    async with engine.begin() as connection:
        await _initialize_schema(
            connection=connection,
            use_migrations=sqla_use_migrations,
            migration_callback=sqla_migration_callback,
            alembic_config_path=sqla_alembic_config_path,
            migration_target=sqla_migration_target,
        )

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def sqla_main_session(
    sqla_main_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    connection = await sqla_main_engine.connect()
    transaction = await connection.begin()

    session = AsyncSession(
        bind=connection,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    await connection.begin_nested()

    @event.listens_for(session.sync_session, "after_transaction_end")
    def _restart_savepoint(_sync_session: Any, _transaction: Any) -> None:
        sync_connection = connection.sync_connection
        if connection.closed or sync_connection is None:
            return
        if (
            sync_connection.in_transaction()
            and not sync_connection.in_nested_transaction()
        ):
            sync_connection.begin_nested()

    try:
        yield session
    finally:
        event.remove(session.sync_session, "after_transaction_end", _restart_savepoint)
        session.expunge_all()
        await session.close()
        if transaction.is_active:
            await transaction.rollback()
        if not connection.closed:
            await connection.close()


@pytest.fixture
def sqla_data_mapping() -> dict[str, ModelMapping]:
    return {}


@pytest_asyncio.fixture
async def sqla_test_data(
    sqla_main_session: AsyncSession,
    sqla_data_mapping: dict[str, ModelMapping],
) -> AsyncGenerator[dict[str, ModelMapping], None]:
    for model in sqla_data_mapping.values():
        for obj in model.values():
            sqla_main_session.add(obj)
    await sqla_main_session.commit()

    for model in sqla_data_mapping.values():
        for obj in model.values():
            await sqla_main_session.refresh(obj)

    yield sqla_data_mapping
