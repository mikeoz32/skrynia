class SkrySqlaError(Exception):
    """Base package exception."""


class PersistenceError(SkrySqlaError):
    """Raised when a transactional database operation fails."""


__all__ = ["SkrySqlaError", "PersistenceError"]
