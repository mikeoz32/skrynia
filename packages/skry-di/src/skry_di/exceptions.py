from __future__ import annotations

from typing import Any


class DIError(Exception):
    """Base class for all container errors."""


class ProviderNotFoundError(DIError):
    def __init__(self, token: Any) -> None:
        super().__init__(f"No provider registered for token: {token!r}")


class ProviderAlreadyRegisteredError(DIError):
    def __init__(self, token: Any) -> None:
        super().__init__(f"Provider already registered for token: {token!r}")


class ScopeError(DIError):
    """Raised when scoped resolution is used without an active scope."""

