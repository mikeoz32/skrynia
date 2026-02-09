from __future__ import annotations

import os
from collections.abc import AsyncGenerator, Mapping
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

from .model import Base

ModelMapping = Mapping[str, Any]


@pytest.fixture(scope="session")
def sqla_test_database_uri() -> str:
    return os.getenv("SKRY_SQLA_TEST_DATABASE_URI", "sqlite+aiosqlite:///:memory:")


@pytest_asyncio.fixture(scope="session")
async def sqla_main_engine(
    sqla_test_database_uri: str,
) -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(sqla_test_database_uri)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def sqla_main_session(
    sqla_main_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    session = AsyncSession(
        bind=sqla_main_engine,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    try:
        yield session
    finally:
        await session.rollback()
        session.expunge_all()
        await session.close()


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
