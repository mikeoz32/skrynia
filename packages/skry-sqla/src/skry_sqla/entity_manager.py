from typing import Sequence, Type, TypeVar, Union

from sqlalchemy import Result, Select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

DB = TypeVar("DB", bound=DeclarativeBase)


class AsyncEntityManager:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def execute_query(self, statement: Select) -> Result:
        return await self.session.execute(statement)

    async def get_one_or_none(self, statement: Select) -> Union[DB, None]:
        result = await self.execute_query(statement)
        return result.unique().scalar_one_or_none()

    async def delete(self, entity):
        self.session.delete(entity)
        try:
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            raise e

    async def save(self, entity):
        self.session.add(entity)
        try:
            await self.session.commit()
            await self.session.refresh(entity)
            return entity
        except Exception as e:
            await self.session.rollback()
            raise e

    async def insert_mamy(
        self,
        model: Type[DeclarativeBase],
        values: Sequence[dict],
        returning: list[str] = ["id"],
    ):
        stmt = insert(model).returning(*[getattr(model, f) for f in returning])
        result = await self.session.execute(stmt, values)
        await self.session.commit()
        return list(result.mappings().fetchall())


__all__ = ["AsyncEntityManager"]
