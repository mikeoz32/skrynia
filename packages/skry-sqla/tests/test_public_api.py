import skry_sqla
from skry_sqla.entity_manager import AsyncEntityManager
from skry_sqla.model import Base, CreatedUpdatedAtMixin, IDMixin, UUIDIDMixin
from skry_sqla.repository import AsyncRepository


def test_public_exports() -> None:
    assert skry_sqla.AsyncEntityManager is AsyncEntityManager
    assert skry_sqla.AsyncRepository is AsyncRepository
    assert skry_sqla.Base is Base
    assert skry_sqla.IDMixin is IDMixin
    assert skry_sqla.UUIDIDMixin is UUIDIDMixin
    assert skry_sqla.CreatedUpdatedAtMixin is CreatedUpdatedAtMixin


def test_version_is_present() -> None:
    assert isinstance(skry_sqla.__version__, str)
    assert skry_sqla.__version__
