from __future__ import annotations

import pytest
from skry_sqla.filters import (
    And,
    ArrayContains,
    ArrayOverlap,
    Between,
    ClauseFilter,
    Contains,
    EndsWith,
    Equal,
    GreaterOrEqual,
    GreaterThan,
    ILike,
    IsNotNull,
    IsNull,
    JsonContains,
    JsonHasKey,
    LessOrEqual,
    LessThan,
    Like,
    Not,
    NotEqual,
    NotIn,
    Or,
    StartsWith,
)
from sqlalchemy import String, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class PgBase(DeclarativeBase):
    pass


class PgEntity(PgBase):
    __tablename__ = "pg_entity"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    nickname: Mapped[str | None] = mapped_column(String, nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String))


def _compile_postgres(statement) -> str:
    return str(statement.compile(dialect=postgresql.dialect()))


def test_between_filter_generates_between_clause() -> None:
    statement = Between("name", "a", "m").apply(select(PgEntity), PgEntity)
    sql = _compile_postgres(statement)
    assert " BETWEEN " in sql


def test_ilike_filter_generates_ilike_clause() -> None:
    statement = ILike("name", "jo%").apply(select(PgEntity), PgEntity)
    sql = _compile_postgres(statement)
    assert " ILIKE " in sql


def test_starts_with_filter_generates_like_clause() -> None:
    statement = StartsWith("name", "jo").apply(select(PgEntity), PgEntity)
    sql = _compile_postgres(statement)
    assert " LIKE " in sql


def test_not_in_filter_generates_not_in_clause() -> None:
    statement = NotIn("name", ["a", "b"]).apply(select(PgEntity), PgEntity)
    sql = _compile_postgres(statement)
    assert " NOT IN " in sql


def test_json_contains_filter_uses_postgres_operator() -> None:
    statement = JsonContains("payload", {"role": "admin"}).apply(
        select(PgEntity), PgEntity
    )
    sql = _compile_postgres(statement)
    assert " @> " in sql


def test_json_has_key_filter_uses_postgres_operator() -> None:
    statement = JsonHasKey("payload", "role").apply(select(PgEntity), PgEntity)
    sql = _compile_postgres(statement)
    assert " ? " in sql


def test_array_contains_filter_uses_postgres_operator() -> None:
    statement = ArrayContains("tags", ["x"]).apply(select(PgEntity), PgEntity)
    sql = _compile_postgres(statement)
    assert " @> " in sql


def test_array_overlap_filter_uses_postgres_operator() -> None:
    statement = ArrayOverlap("tags", ["x"]).apply(select(PgEntity), PgEntity)
    sql = _compile_postgres(statement)
    assert " && " in sql


def test_logical_filters_compose_into_single_where_expression() -> None:
    statement = Or(
        [
            Equal("name", "alpha"),
            And([Not(IsNull("nickname")), Equal("name", "beta")]),
        ]
    ).apply(select(PgEntity), PgEntity)
    sql = _compile_postgres(statement)
    assert " OR " in sql
    assert " AND " in sql
    assert " IS NOT NULL" in sql


def test_unknown_field_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unknown field"):
        Equal("missing", "x").apply(select(PgEntity), PgEntity)


@pytest.mark.parametrize(
    ("filter_item", "token"),
    [
        (Like("name", "%ha%"), " LIKE "),
        (NotEqual("name", "x"), " !="),
        (GreaterThan("name", "a"), " > "),
        (LessThan("name", "z"), " < "),
        (GreaterOrEqual("name", "a"), " >= "),
        (LessOrEqual("name", "z"), " <= "),
        (IsNotNull("nickname"), " IS NOT NULL"),
        (EndsWith("name", "ha"), " LIKE "),
        (Contains("name", "alp"), " LIKE "),
    ],
)
def test_additional_filters_compile(filter_item: ClauseFilter, token: str) -> None:
    statement = filter_item.apply(select(PgEntity), PgEntity)
    sql = _compile_postgres(statement)
    assert token in sql


def test_base_clause_filter_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        ClauseFilter().to_clause(PgEntity)
