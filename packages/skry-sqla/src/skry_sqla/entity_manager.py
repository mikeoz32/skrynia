from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, List, TypeVar

from sqlalchemy import Result, insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import Executable

from .exceptions import PersistenceError

DB = TypeVar("DB", bound=DeclarativeBase)


class AsyncEntityManager:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def execute_query(self, statement: Executable) -> Result[Any]:
        return await self.session.execute(statement)

    async def get_one_or_none(self, statement: Executable) -> DB | None:
        result = await self.execute_query(statement)
        return result.unique().scalar_one_or_none()

    async def list(self, statement: Executable) -> list[DB]:
        result = await self.execute_query(statement)
        return list(result.scalars().all())

    async def delete(self, entity: DB) -> None:
        await self.session.delete(entity)
        try:
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise PersistenceError("Failed to delete entity") from e

    async def save(self, entity: DB) -> DB:
        self.session.add(entity)
        try:
            await self.session.commit()
            await self.session.refresh(entity)
            return entity
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise PersistenceError("Failed to save entity") from e

    async def insert_many(
        self,
        model: type[DeclarativeBase],
        values: Sequence[Mapping[str, Any]],
        returning: Sequence[str] | None = None,
    ) -> List[dict[str, Any]]:
        returning_fields = list(returning or ["id"])
        stmt = insert(model).returning(*[getattr(model, f) for f in returning_fields])
        try:
            result = await self.session.execute(stmt, values)
            await self.session.commit()
            return [dict(row) for row in result.mappings().all()]
        except SQLAlchemyError as e:
            await self.session.rollback()
            raise PersistenceError("Failed to insert entities in bulk") from e

    async def insert_mamy(  # pragma: no cover
        self,
        model: type[DeclarativeBase],
        values: Sequence[Mapping[str, Any]],
        returning: Sequence[str] | None = None,
    ) -> List[dict[str, Any]]:
        return await self.insert_many(model=model, values=values, returning=returning)


__all__ = ["AsyncEntityManager"]
