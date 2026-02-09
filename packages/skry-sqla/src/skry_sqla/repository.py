from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, ClassVar, Generic, List, TypeVar, cast

from sqlalchemy import Select, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, joinedload
from sqlalchemy.sql import Executable

from .entity_manager import AsyncEntityManager
from .filters import Filter

DB = TypeVar("DB", bound=DeclarativeBase)
SelectOptions = Sequence[Any] | None


def apply_options(
    statement: Select[Any], options: SelectOptions = None
) -> Select[Any]:
    if options is not None:
        statement = statement.options(*options)
    return statement


class QueryBuilder(Generic[DB]):
    def __init__(
        self, entity_type: type[DB], fields: Sequence[str] | None = None
    ) -> None:
        self.entity_type = entity_type
        if fields:
            self.statement = select(*[self._get_field(name) for name in fields])
        else:
            self.statement = select(entity_type)

    def where(self, filters: Sequence[Filter] | None = None) -> QueryBuilder[DB]:
        for item in filters or []:
            self.statement = item.apply(self.statement, self.entity_type)
        return self

    def order_by(self, order: Sequence[str] | None = None) -> QueryBuilder[DB]:
        if not order:
            return self

        clauses: list[Any] = []
        for field in order:
            direction = asc
            field_name = field
            if field.startswith("-"):
                field_name = field[1:]
                direction = desc
            clauses.append(direction(self._get_field(field_name)))
        self.statement = self.statement.order_by(*clauses)
        return self

    def relations(self, relations: Sequence[str] | None = None) -> QueryBuilder[DB]:
        for relation in relations or []:
            if not hasattr(self.entity_type, relation):
                raise ValueError(f"Unknown relation '{relation}'")
            relation_attr = self._get_field(relation)
            self.statement = self.statement.options(joinedload(relation_attr))
        return self

    def build(self) -> Select[Any]:
        return self.statement

    def _get_field(self, name: str) -> Any:
        if not hasattr(self.entity_type, name):
            raise ValueError(f"Unknown field '{name}'")
        return getattr(self.entity_type, name)


class AsyncRepository(Generic[DB]):
    model: ClassVar[type[DB]]

    def __init__(self, session: AsyncSession) -> None:
        if getattr(self.__class__, "model", None) is None:
            raise ValueError(
                f"{self.__class__.__name__}.model is not set. "
                "Define class attribute `model`."
            )
        self.entity_manager = AsyncEntityManager(session)

    async def add(self, entity: DB) -> DB:
        return cast(DB, await self.entity_manager.save(entity))

    async def save(self, entity: DB) -> DB:
        return cast(DB, await self.entity_manager.save(entity))

    def create(self, **kwargs: Any) -> DB:
        return self.model(**kwargs)

    def patch(self, entity: DB, data: Mapping[str, Any]) -> DB:
        for field, value in data.items():
            setattr(entity, field, value)
        return entity

    async def all(self, options: SelectOptions = None) -> list[DB]:
        statement = apply_options(select(self.model), options)
        return await self.list(statement)

    async def find(
        self,
        filters: Sequence[Filter] | None = None,
        order_by: Sequence[str] | None = None,
        relations: Sequence[str] | None = None,
    ) -> list[DB]:
        statement = (
            QueryBuilder(self.model)
            .where(filters)
            .order_by(order_by)
            .relations(relations)
            .build()
        )
        return await self.list(statement)

    async def find_and_count(
        self,
        filters: Sequence[Filter] | None = None,
        order_by: Sequence[str] | None = None,
        relations: Sequence[str] | None = None,
    ) -> tuple[list[DB], int]:
        items = await self.find(
            filters=filters,
            order_by=order_by,
            relations=relations,
        )
        total = await self.count(filters=filters)
        return items, total

    async def find_one(
        self,
        filters: Sequence[Filter] | None = None,
        relations: Sequence[str] | None = None,
    ) -> DB | None:
        statement = QueryBuilder(self.model).where(filters).relations(relations).build()
        return await self.get_one_or_none(statement)

    async def get_one_or_none(self, statement: Executable) -> DB | None:
        return cast(DB | None, await self.entity_manager.get_one_or_none(statement))

    async def get_by_id(
        self, id_value: Any, options: SelectOptions = None
    ) -> DB | None:
        if not hasattr(self.model, "id"):
            raise ValueError(f"{self.model.__name__} does not define id attribute")

        model_with_id = cast(Any, self.model)
        statement = select(self.model).where(model_with_id.id == id_value)
        statement = apply_options(statement, options)
        return await self.get_one_or_none(statement)

    async def list(self, statement: Executable) -> list[DB]:
        return cast(list[DB], await self.entity_manager.list(statement))

    async def count(self, filters: Sequence[Filter] | None = None) -> int:
        statement = select(func.count()).select_from(self.model)
        for item in filters or []:
            statement = item.apply(statement, self.model)

        result = await self.entity_manager.execute_query(statement)
        value = result.scalar_one()
        return int(value)

    async def exists(self, filters: Sequence[Filter] | None = None) -> bool:
        return (await self.count(filters=filters)) > 0

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


__all__ = ["SelectOptions", "apply_options", "QueryBuilder", "AsyncRepository"]
