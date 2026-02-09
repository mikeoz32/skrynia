from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Generic, List, TypeVar, cast

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import Executable

from .entity_manager import AsyncEntityManager

DB = TypeVar("DB", bound=DeclarativeBase)


class AsyncRepository(Generic[DB]):
    def __init__(self, session: AsyncSession, model: type[DB]) -> None:
        self.model = model
        self.entity_manager = AsyncEntityManager(session)

    async def add(self, entity: DB) -> DB:
        return cast(DB, await self.entity_manager.save(entity))

    async def get_one_or_none(self, statement: Executable) -> DB | None:
        return cast(DB | None, await self.entity_manager.get_one_or_none(statement))

    async def list(self, statement: Executable) -> list[DB]:
        return cast(list[DB], await self.entity_manager.list(statement))

    async def delete(self, entity: DB) -> None:
        await self.entity_manager.delete(entity)

    async def insert_many(
        self,
        values: Sequence[Mapping[str, Any]],
        returning: Sequence[str] | None = None,
    ) -> List[dict[str, Any]]:
        return await self.entity_manager.insert_many(
            model=self.model,
            values=values,
            returning=returning,
        )


__all__ = ["AsyncRepository"]
