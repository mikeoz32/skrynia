from __future__ import annotations

import pytest
from model import User
from sqlalchemy import select, text

pytestmark = pytest.mark.asyncio


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
