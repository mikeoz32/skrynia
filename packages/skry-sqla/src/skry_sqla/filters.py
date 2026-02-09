from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

from sqlalchemy import and_, not_, or_
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import Select


def _get_field(model: type[DeclarativeBase], field: str) -> Any:
    if not hasattr(model, field):
        raise ValueError(f"Unknown field '{field}'")
    return getattr(model, field)


class Filter(Protocol):
    def apply(self, stmt: Select[Any], model: type[DeclarativeBase]) -> Select[Any]: ...


class ClauseFilter:
    def to_clause(self, model: type[DeclarativeBase]) -> Any:
        raise NotImplementedError

    def apply(self, stmt: Select[Any], model: type[DeclarativeBase]) -> Select[Any]:
        return stmt.where(self.to_clause(model))


class Equal(ClauseFilter):
    def __init__(self, field: str, value: Any) -> None:
        self.field = field
        self.value = value

    def to_clause(self, model: type[DeclarativeBase]) -> Any:
        return _get_field(model, self.field) == self.value


class In(ClauseFilter):
    def __init__(self, field: str, values: list[Any]) -> None:
        self.field = field
        self.values = values

    def to_clause(self, model: type[DeclarativeBase]) -> Any:
        return _get_field(model, self.field).in_(self.values)


class Like(ClauseFilter):
    def __init__(self, field: str, pattern: str) -> None:
        self.field = field
        self.pattern = pattern

    def to_clause(self, model: type[DeclarativeBase]) -> Any:
        return _get_field(model, self.field).like(self.pattern)


class NotEqual(ClauseFilter):
    def __init__(self, field: str, value: Any) -> None:
        self.field = field
        self.value = value

    def to_clause(self, model: type[DeclarativeBase]) -> Any:
        return _get_field(model, self.field) != self.value


class GreaterThan(ClauseFilter):
    def __init__(self, field: str, value: Any) -> None:
        self.field = field
        self.value = value

    def to_clause(self, model: type[DeclarativeBase]) -> Any:
        return _get_field(model, self.field) > self.value


class LessThan(ClauseFilter):
    def __init__(self, field: str, value: Any) -> None:
        self.field = field
        self.value = value

    def to_clause(self, model: type[DeclarativeBase]) -> Any:
        return _get_field(model, self.field) < self.value


class GreaterOrEqual(ClauseFilter):
    def __init__(self, field: str, value: Any) -> None:
        self.field = field
        self.value = value

    def to_clause(self, model: type[DeclarativeBase]) -> Any:
        return _get_field(model, self.field) >= self.value


class LessOrEqual(ClauseFilter):
    def __init__(self, field: str, value: Any) -> None:
        self.field = field
        self.value = value

    def to_clause(self, model: type[DeclarativeBase]) -> Any:
        return _get_field(model, self.field) <= self.value


class Between(ClauseFilter):
    def __init__(self, field: str, start: Any, end: Any) -> None:
        self.field = field
        self.start = start
        self.end = end

    def to_clause(self, model: type[DeclarativeBase]) -> Any:
        return _get_field(model, self.field).between(self.start, self.end)


class IsNull(ClauseFilter):
    def __init__(self, field: str) -> None:
        self.field = field

    def to_clause(self, model: type[DeclarativeBase]) -> Any:
        return _get_field(model, self.field).is_(None)


class IsNotNull(ClauseFilter):
    def __init__(self, field: str) -> None:
        self.field = field

    def to_clause(self, model: type[DeclarativeBase]) -> Any:
        return _get_field(model, self.field).is_not(None)


class ILike(ClauseFilter):
    def __init__(self, field: str, pattern: str) -> None:
        self.field = field
        self.pattern = pattern

    def to_clause(self, model: type[DeclarativeBase]) -> Any:
        return _get_field(model, self.field).ilike(self.pattern)


class StartsWith(ClauseFilter):
    def __init__(self, field: str, value: str) -> None:
        self.field = field
        self.value = value

    def to_clause(self, model: type[DeclarativeBase]) -> Any:
        return _get_field(model, self.field).startswith(self.value)


class EndsWith(ClauseFilter):
    def __init__(self, field: str, value: str) -> None:
        self.field = field
        self.value = value

    def to_clause(self, model: type[DeclarativeBase]) -> Any:
        return _get_field(model, self.field).endswith(self.value)


class Contains(ClauseFilter):
    def __init__(self, field: str, value: str) -> None:
        self.field = field
        self.value = value

    def to_clause(self, model: type[DeclarativeBase]) -> Any:
        return _get_field(model, self.field).contains(self.value)


class NotIn(ClauseFilter):
    def __init__(self, field: str, values: list[Any]) -> None:
        self.field = field
        self.values = values

    def to_clause(self, model: type[DeclarativeBase]) -> Any:
        return _get_field(model, self.field).notin_(self.values)


class JsonContains(ClauseFilter):
    def __init__(self, field: str, value: Any) -> None:
        self.field = field
        self.value = value

    def to_clause(self, model: type[DeclarativeBase]) -> Any:
        return _get_field(model, self.field).contains(self.value)


class JsonHasKey(ClauseFilter):
    def __init__(self, field: str, key: str) -> None:
        self.field = field
        self.key = key

    def to_clause(self, model: type[DeclarativeBase]) -> Any:
        return _get_field(model, self.field).has_key(self.key)


class ArrayContains(ClauseFilter):
    def __init__(self, field: str, values: list[Any]) -> None:
        self.field = field
        self.values = values

    def to_clause(self, model: type[DeclarativeBase]) -> Any:
        return _get_field(model, self.field).contains(self.values)


class ArrayOverlap(ClauseFilter):
    def __init__(self, field: str, values: list[Any]) -> None:
        self.field = field
        self.values = values

    def to_clause(self, model: type[DeclarativeBase]) -> Any:
        return _get_field(model, self.field).overlap(self.values)


class And(ClauseFilter):
    def __init__(self, filters: Sequence[ClauseFilter]) -> None:
        self.filters = list(filters)

    def to_clause(self, model: type[DeclarativeBase]) -> Any:
        return and_(*[item.to_clause(model) for item in self.filters])


class Or(ClauseFilter):
    def __init__(self, filters: Sequence[ClauseFilter]) -> None:
        self.filters = list(filters)

    def to_clause(self, model: type[DeclarativeBase]) -> Any:
        return or_(*[item.to_clause(model) for item in self.filters])


class Not(ClauseFilter):
    def __init__(self, filter_item: ClauseFilter) -> None:
        self.filter_item = filter_item

    def to_clause(self, model: type[DeclarativeBase]) -> Any:
        return not_(self.filter_item.to_clause(model))


__all__ = [
    "Filter",
    "Equal",
    "In",
    "Like",
    "NotEqual",
    "GreaterThan",
    "LessThan",
    "GreaterOrEqual",
    "LessOrEqual",
    "Between",
    "IsNull",
    "IsNotNull",
    "ILike",
    "StartsWith",
    "EndsWith",
    "Contains",
    "NotIn",
    "JsonContains",
    "JsonHasKey",
    "ArrayContains",
    "ArrayOverlap",
    "And",
    "Or",
    "Not",
]

