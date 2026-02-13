from __future__ import annotations

import pytest
from model import User
from skry_sqla.pytest_plugin import (
    _initialize_schema,
    _resolve_bool_setting,
    _resolve_string_setting,
)
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine


@pytest.mark.asyncio
async def test_sqla_main_session_fixture_runs_query(sqla_main_session) -> None:
    result = await sqla_main_session.execute(text("SELECT 1"))
    assert result.scalar() == 1


@pytest.fixture
def sqla_data_mapping() -> dict[str, dict[str, User]]:
    return {
        "users": {
            "user_1": User(email="plugin-user-1@test.com", name="Plugin User 1"),
            "user_2": User(email="plugin-user-2@test.com", name="Plugin User 2"),
        }
    }


@pytest.mark.asyncio
async def test_sqla_test_data_fixture_loads_models(
    sqla_test_data, sqla_main_session
) -> None:
    result = await sqla_main_session.execute(
        select(User).where(User.email.like("plugin-user-%"))
    )
    rows = list(result.scalars().all())

    assert len(rows) == 2
    assert {row.email for row in rows} == {
        "plugin-user-1@test.com",
        "plugin-user-2@test.com",
    }


@pytest.mark.asyncio
async def test_initialize_schema_uses_custom_migrations() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    callback_calls = 0

    async def migration_callback(connection) -> None:
        nonlocal callback_calls
        callback_calls += 1
        await connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY)"))

    async with engine.begin() as connection:
        await _initialize_schema(
            connection=connection,
            use_migrations=True,
            migration_callback=migration_callback,
            alembic_config_path=None,
            migration_target="head",
        )

    async with engine.begin() as connection:
        result = await connection.execute(
            text(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='users'"
            )
        )
        table_name = result.scalar_one_or_none()

    await engine.dispose()

    assert callback_calls == 1
    assert table_name == "users"


@pytest.mark.asyncio
async def test_initialize_schema_requires_alembic_config() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    with pytest.raises(RuntimeError, match="sqla_alembic_config_path"):
        async with engine.begin() as connection:
            await _initialize_schema(
                connection=connection,
                use_migrations=True,
                migration_callback=None,
                alembic_config_path=None,
                migration_target="head",
            )

    await engine.dispose()


@pytest.mark.asyncio
async def test_sqla_main_session_commit_does_not_fail(sqla_main_session) -> None:
    sqla_main_session.add(
        User(email="plugin-isolation@test.com", name="Isolation Marker")
    )
    await sqla_main_session.commit()


@pytest.mark.asyncio
async def test_sqla_main_session_isolation_between_tests(sqla_main_session) -> None:
    result = await sqla_main_session.execute(
        select(User).where(User.email == "plugin-isolation@test.com")
    )
    rows = list(result.scalars().all())
    assert rows == []


class _FakePytestConfig:
    def __init__(self, options: dict[str, object], ini: dict[str, object]) -> None:
        self._options = options
        self._ini = ini

    def getoption(self, name: str) -> object:
        return self._options.get(name)

    def getini(self, name: str) -> object:
        return self._ini.get(name, "")


def test_resolve_string_setting_prefers_cli_over_ini() -> None:
    config = _FakePytestConfig(
        options={"sqla_test_database_uri": "sqlite+aiosqlite:///cli.db"},
        ini={"sqla_test_database_uri": "sqlite+aiosqlite:///ini.db"},
    )
    value = _resolve_string_setting(
        pytestconfig=config,
        option_name="sqla_test_database_uri",
        ini_name="sqla_test_database_uri",
        default="sqlite+aiosqlite:///:memory:",
    )
    assert value == "sqlite+aiosqlite:///cli.db"


def test_resolve_string_setting_uses_default_for_empty_values() -> None:
    config = _FakePytestConfig(options={"sqla_alembic_config_path": ""}, ini={})
    value = _resolve_string_setting(
        pytestconfig=config,
        option_name="sqla_alembic_config_path",
        ini_name="sqla_alembic_config_path",
        default="",
    )
    assert value == ""


def test_resolve_bool_setting_prefers_cli_when_present() -> None:
    config = _FakePytestConfig(
        options={"sqla_use_migrations": True},
        ini={"sqla_use_migrations": False},
    )
    value = _resolve_bool_setting(
        pytestconfig=config,
        option_name="sqla_use_migrations",
        ini_name="sqla_use_migrations",
        default=False,
    )
    assert value is True


def test_resolve_bool_setting_falls_back_to_ini() -> None:
    config = _FakePytestConfig(options={"sqla_use_migrations": None}, ini={})
    value = _resolve_bool_setting(
        pytestconfig=config,
        option_name="sqla_use_migrations",
        ini_name="sqla_use_migrations",
        default=False,
    )
    assert value is False
