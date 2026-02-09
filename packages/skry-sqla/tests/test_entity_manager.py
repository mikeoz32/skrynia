import pytest
from model import User
from skry_sqla.entity_manager import AsyncEntityManager
from sqlalchemy import select, text

pytestmark = pytest.mark.asyncio


async def test_execute_query(session):
    em = AsyncEntityManager(session)
    result = await em.execute_query(text("SELECT 1"))
    assert result.scalar() == 1


async def test_save(session):
    em = AsyncEntityManager(session)

    saved = await em.save(User(email="test@test.com", name="test"))

    assert saved.id is not None

    retrieved = await em.get_one_or_none(
        select(User).where(User.email == "test@test.com")
    )
    assert retrieved


async def test_get_nonexistent(session):
    em = AsyncEntityManager(session)

    nonexisted = await em.get_one_or_none(
        select(User).where(User.email == "qwe@qwe.qw")
    )

    assert nonexisted is None
