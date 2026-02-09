import pytest
from model import User
from skry_sqla.exceptions import PersistenceError
from skry_sqla.filters import Equal, GreaterThan, In, LessThan, Like, NotEqual
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


async def test_create_and_all(session) -> None:
    repo = UserRepository(session)

    user = repo.create(email="all-created@test.com", name="created")
    await repo.add(user)

    items = await repo.all()

    assert any(item.email == "all-created@test.com" for item in items)


async def test_find_applies_filters_and_order(session) -> None:
    repo = UserRepository(session)
    await repo.add(User(email="find-a@test.com", name="alpha"))
    await repo.add(User(email="find-b@test.com", name="beta"))
    await repo.add(User(email="find-c@test.com", name="skip"))

    items = await repo.find(
        filters=[Like("email", "find-%"), NotEqual("name", "skip")],
        order_by=["-email"],
    )

    assert [item.email for item in items] == ["find-b@test.com", "find-a@test.com"]


async def test_find_one_returns_first_match(session) -> None:
    repo = UserRepository(session)
    await repo.add(User(email="find-one@test.com", name="single"))

    item = await repo.find_one(filters=[Equal("email", "find-one@test.com")])

    assert item is not None
    assert item.name == "single"


async def test_find_supports_in_and_range_filters(session) -> None:
    repo = UserRepository(session)
    await repo.add(User(email="range-a@test.com", name="range-a"))
    await repo.add(User(email="range-b@test.com", name="range-b"))
    await repo.add(User(email="range-c@test.com", name="range-c"))

    items = await repo.find(
        filters=[
            In("email", ["range-a@test.com", "range-b@test.com", "range-c@test.com"]),
            GreaterThan("name", "range-a"),
            LessThan("name", "range-c"),
        ]
    )

    assert {item.email for item in items} == {"range-b@test.com"}


async def test_find_raises_for_unknown_field(session) -> None:
    repo = UserRepository(session)

    with pytest.raises(ValueError, match="Unknown field"):
        await repo.find(filters=[Equal("missing_field", "x")])


async def test_find_raises_for_unknown_relation(session) -> None:
    repo = UserRepository(session)

    with pytest.raises(ValueError, match="Unknown relation"):
        await repo.find(relations=["missing_relation"])


async def test_save_alias_and_get_by_id(session) -> None:
    repo = UserRepository(session)

    user = await repo.save(User(email="save-alias@test.com", name="save"))
    loaded = await repo.get_by_id(user.id)

    assert loaded is not None
    assert loaded.email == "save-alias@test.com"


async def test_patch_and_save_updates_entity(session) -> None:
    repo = UserRepository(session)
    user = await repo.add(User(email="patch@test.com", name="before"))

    updated = await repo.save(repo.patch(user, {"name": "after"}))

    assert updated.name == "after"
    loaded = await repo.get_by_id(updated.id)
    assert loaded is not None
    assert loaded.name == "after"


async def test_count_and_exists(session) -> None:
    repo = UserRepository(session)
    await repo.add(User(email="count-a@test.com", name="count"))
    await repo.add(User(email="count-b@test.com", name="count"))

    count = await repo.count(filters=[Like("email", "count-%")])
    exists = await repo.exists(filters=[Equal("email", "count-a@test.com")])
    missing = await repo.exists(filters=[Equal("email", "count-missing@test.com")])

    assert count == 2
    assert exists is True
    assert missing is False


async def test_find_and_count_returns_items_and_total(session) -> None:
    repo = UserRepository(session)
    await repo.add(User(email="fac-a@test.com", name="a"))
    await repo.add(User(email="fac-b@test.com", name="b"))
    await repo.add(User(email="other@test.com", name="c"))

    items, total = await repo.find_and_count(
        filters=[Like("email", "fac-%")],
        order_by=["email"],
    )

    assert total == 2
    assert [item.email for item in items] == ["fac-a@test.com", "fac-b@test.com"]


async def test_find_and_count_empty_result(session) -> None:
    repo = UserRepository(session)
    items, total = await repo.find_and_count(
        filters=[Equal("email", "missing@test.com")]
    )

    assert items == []
    assert total == 0
