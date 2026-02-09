# skry-sqla

`skry-sqla` is a typed helper library for async SQLAlchemy projects.
It provides:

- reusable model mixins (`IDMixin`, `UUIDIDMixin`, timestamp mixins)
- `AsyncEntityManager` for transactional CRUD helpers
- `AsyncRepository` as a thin generic repository abstraction

## Installation

From this workspace:

```bash
uv sync --all-packages --all-groups
```

As a standalone dependency:

```bash
uv add skry-sqla
```

## Quick Start

```python
from sqlalchemy import String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from skry_sqla import AsyncRepository, Base, IDMixin


class User(Base, IDMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)


async def create_user(session: AsyncSession) -> User:
    repo = AsyncRepository(session, User)
    user = await repo.add(User(email="john@example.com", name="John"))
    return user


async def get_user(session: AsyncSession) -> User | None:
    repo = AsyncRepository(session, User)
    return await repo.get_one_or_none(
        select(User).where(User.email == "john@example.com")
    )
```

## Public API

- `AsyncEntityManager`
- `AsyncRepository`
- `Base`
- `IDMixin`, `UUIDIDMixin`
- `CreatedAtMixin`, `UpdatedAtMixin`, `CreatedUpdatedAtMixin`
- `TimestamableMixin`
- `SkrySqlaError`, `PersistenceError`

## Development

Run tests and quality checks from the repository root:

```bash
uv run pytest
uv run ruff check .
uv run mypy
```

## Pytest Plugin

Use `skry_sqla.pytest_plugin` fixtures in tests via:

```python
pytest_plugins = ("skry_sqla.pytest_plugin",)
```

Schema setup modes:

- default metadata mode: creates tables with `Base.metadata.create_all`
- migration mode: set `SKRY_SQLA_USE_MIGRATIONS=1`

When migration mode is enabled, provide either:

- `SKRY_SQLA_ALEMBIC_CONFIG=/path/to/alembic.ini` (runs `upgrade head` by default)
- custom `sqla_migration_callback` fixture (runs once per test session)

Optional env vars:

- `SKRY_SQLA_MIGRATION_TARGET` (default: `head`)
- `SKRY_SQLA_TEST_DATABASE_URI`
