from importlib.metadata import PackageNotFoundError, version

from .entity_manager import AsyncEntityManager
from .exceptions import PersistenceError, SkrySqlaError
from .model import (
    M_ID,
    M_TS,
    M_UID,
    Base,
    CreatedAtMixin,
    CreatedUpdatedAtMixin,
    IDMixin,
    M,
    TimestamableMixin,
    TimestampableMixin,
    UpdatedAtMixin,
    UUIDIDMixin,
)
from .repository import AsyncRepository

try:
    __version__ = version("skry-sqla")
except PackageNotFoundError:
    __version__ = "0.1.0"

__all__ = [
    "__version__",
    "AsyncEntityManager",
    "AsyncRepository",
    "Base",
    "CreatedAtMixin",
    "CreatedUpdatedAtMixin",
    "IDMixin",
    "M",
    "M_ID",
    "M_UID",
    "M_TS",
    "PersistenceError",
    "SkrySqlaError",
    "TimestampableMixin",
    "TimestamableMixin",
    "UpdatedAtMixin",
    "UUIDIDMixin",
]
