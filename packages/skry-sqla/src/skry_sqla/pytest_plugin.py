from __future__ import annotations

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


def pytest_addoption(parser: Any) -> None:
    group = parser.getgroup("skry-sqla")

    parser.addini(
        "sqla_test_database_uri",
        "Database URI for skry-sqla pytest plugin.",
        default="sqlite+aiosqlite:///:memory:",
    )
    parser.addini(
        "sqla_use_migrations",
        "Enable migration mode for skry-sqla pytest plugin.",
        type="bool",
        default=False,
    )
    parser.addini(
        "sqla_alembic_config_path",
        "Path to Alembic config for skry-sqla pytest plugin.",
        default="",
    )
    parser.addini(
        "sqla_migration_target",
        "Alembic target revision for skry-sqla pytest plugin.",
        default="head",
    )

    group.addoption(
        "--sqla-test-database-uri",
        action="store",
        dest="sqla_test_database_uri",
        default=None,
        help="Override sqla_test_database_uri.",
    )
    group.addoption(
        "--sqla-use-migrations",
        action="store_true",
        dest="sqla_use_migrations",
        default=None,
        help="Enable migration mode.",
    )
    group.addoption(
        "--sqla-no-migrations",
        action="store_false",
        dest="sqla_use_migrations",
        help="Disable migration mode.",
    )
    group.addoption(
        "--sqla-alembic-config-path",
        action="store",
        dest="sqla_alembic_config_path",
        default=None,
        help="Override sqla_alembic_config_path.",
    )
    group.addoption(
        "--sqla-migration-target",
        action="store",
        dest="sqla_migration_target",
        default=None,
        help="Override sqla_migration_target.",
    )


def _resolve_string_setting(
    *,
    pytestconfig: Any,
    option_name: str,
    ini_name: str,
    default: str,
) -> str:
    cli_value = pytestconfig.getoption(option_name)
    if cli_value not in (None, ""):
        return str(cli_value)

    ini_value = pytestconfig.getini(ini_name)
    if ini_value not in (None, ""):
        return str(ini_value)

    return default


def _resolve_bool_setting(
    *,
    pytestconfig: Any,
    option_name: str,
    ini_name: str,
    default: bool,
) -> bool:
    cli_value = pytestconfig.getoption(option_name)
    if cli_value is not None:
        return bool(cli_value)

    ini_value = pytestconfig.getini(ini_name)
    if isinstance(ini_value, bool):
        return ini_value
    if ini_value in (None, ""):
        return default
    return str(ini_value).strip().lower() in {"1", "true", "yes", "on"}


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
            "Set sqla_alembic_config_path/--sqla-alembic-config-path or "
            "override sqla_migration_callback."
        )

    await connection.run_sync(
        lambda sync_connection: _run_alembic_upgrade(
            sync_connection=sync_connection,
            alembic_config_path=alembic_config_path,
            migration_target=migration_target,
        )
    )


@pytest.fixture(scope="session")
def sqla_test_database_uri(pytestconfig: pytest.Config) -> str:
    return _resolve_string_setting(
        pytestconfig=pytestconfig,
        option_name="sqla_test_database_uri",
        ini_name="sqla_test_database_uri",
        default="sqlite+aiosqlite:///:memory:",
    )


@pytest.fixture(scope="session")
def sqla_use_migrations(pytestconfig: pytest.Config) -> bool:
    return _resolve_bool_setting(
        pytestconfig=pytestconfig,
        option_name="sqla_use_migrations",
        ini_name="sqla_use_migrations",
        default=False,
    )


@pytest.fixture(scope="session")
def sqla_alembic_config_path(pytestconfig: pytest.Config) -> str | None:
    value = _resolve_string_setting(
        pytestconfig=pytestconfig,
        option_name="sqla_alembic_config_path",
        ini_name="sqla_alembic_config_path",
        default="",
    )
    return value or None


@pytest.fixture(scope="session")
def sqla_migration_target(pytestconfig: pytest.Config) -> str:
    return _resolve_string_setting(
        pytestconfig=pytestconfig,
        option_name="sqla_migration_target",
        ini_name="sqla_migration_target",
        default="head",
    )


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
