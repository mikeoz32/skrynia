from __future__ import annotations

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

pytest_plugins = ("skry_sqla.pytest_plugin",)


@pytest_asyncio.fixture
async def session(sqla_main_session: AsyncSession) -> AsyncSession:
    return sqla_main_session
