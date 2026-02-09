from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, TypeVar
from uuid import UUID, uuid4

from sqlalchemy import TIMESTAMP, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

UTC = timezone.utc


def now_utc() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    ...


class BaseModel:
    ...


class IDMixin(BaseModel):
    id: Mapped[Annotated[int, mapped_column(primary_key=True, autoincrement=True)]]


class UUIDIDMixin(BaseModel):
    id: Mapped[Annotated[UUID, mapped_column(Uuid, primary_key=True, default=uuid4)]]


class CreatedAtMixin(BaseModel):
    created_at: Mapped[
        Annotated[
            datetime,
            mapped_column(
                TIMESTAMP(timezone=True),
                server_default=func.now(),
                index=True,
                default=now_utc,
            ),
        ]
    ]


class UpdatedAtMixin(BaseModel):
    updated_at: Mapped[
        Annotated[
            datetime,
            mapped_column(
                TIMESTAMP(timezone=True),
                server_default=func.now(),
                index=True,
                default=now_utc,
                onupdate=now_utc,
            ),
        ]
    ]


class CreatedUpdatedAtMixin(CreatedAtMixin, UpdatedAtMixin):
    ...


class TimestampableMixin(BaseModel):
    timestamp: Mapped[Annotated[datetime, mapped_column(TIMESTAMP(timezone=False))]]


# Backward-compatible alias for previous typo in public API.
TimestamableMixin = TimestampableMixin

M = TypeVar("M", bound=DeclarativeBase)
M_ID = TypeVar("M_ID", bound=IDMixin)
M_UID = TypeVar("M_UID", bound=UUIDIDMixin)
M_TS = TypeVar("M_TS", bound=TimestampableMixin)

__all__ = [
    "Base",
    "IDMixin",
    "UUIDIDMixin",
    "CreatedAtMixin",
    "UpdatedAtMixin",
    "CreatedUpdatedAtMixin",
    "TimestampableMixin",
    "TimestamableMixin",
    "M",
    "M_ID",
    "M_UID",
    "M_TS",
]
