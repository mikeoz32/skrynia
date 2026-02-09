import pytest
from model import User
from skry_sqla.exceptions import PersistenceError
from skry_sqla.repository import AsyncRepository
from sqlalchemy import func, select

pytestmark = pytest.mark.asyncio


class UserRepository(AsyncRepository[User]):
    model = User


class MissingModelRepository(AsyncRepository[User]):
    pass


async def test_add_and_get(session) -> None:
    repo = UserRepository(session)

    saved = await repo.add(User(email="repo-save@test.com", name="repo"))
    loaded = await repo.get_one_or_none(
        select(User).where(User.email == "repo-save@test.com")
    )

    assert saved.id is not None
    assert loaded is not None
    assert loaded.email == "repo-save@test.com"


async def test_list_returns_entities(session) -> None:
    repo = UserRepository(session)
    await repo.add(User(email="repo-list-a@test.com", name="a"))
    await repo.add(User(email="repo-list-b@test.com", name="b"))

    rows = await repo.list(select(User).where(User.email.like("repo-list-%")))

    emails = {item.email for item in rows}
    assert "repo-list-a@test.com" in emails
    assert "repo-list-b@test.com" in emails


async def test_delete_removes_entity(session) -> None:
    repo = UserRepository(session)
    saved = await repo.add(User(email="repo-delete@test.com", name="delete-me"))

    await repo.delete(saved)
    removed = await repo.get_one_or_none(
        select(User).where(User.email == "repo-delete@test.com")
    )

    assert removed is None


async def test_insert_many_returns_requested_fields(session) -> None:
    repo = UserRepository(session)

    inserted = await repo.insert_many(
        [
            {"email": "bulk-a@test.com", "name": "bulk-a"},
            {"email": "bulk-b@test.com", "name": "bulk-b"},
        ],
        returning=["id", "email"],
    )

    assert len(inserted) == 2
    assert all("id" in row for row in inserted)
    assert {row["email"] for row in inserted} == {"bulk-a@test.com", "bulk-b@test.com"}


async def test_add_rolls_back_and_raises_persistence_error(session) -> None:
    repo = UserRepository(session)
    await repo.add(User(email="duplicate@test.com", name="first"))

    with pytest.raises(PersistenceError):
        await repo.add(User(email="duplicate@test.com", name="second"))

    count = await session.scalar(
        select(func.count()).select_from(User).where(User.email == "duplicate@test.com")
    )
    assert count == 1


async def test_missing_model_definition_raises_error(session) -> None:
    with pytest.raises(ValueError, match="model"):
        MissingModelRepository(session)
