from __future__ import annotations

from collections.abc import Callable, Hashable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Any, TypeVar, cast

from typing_extensions import Doc

from .exceptions import (
    ProviderAlreadyRegisteredError,
    ProviderNotFoundError,
    ScopeError,
)

T = TypeVar("T")
ProviderFactory = Callable[[Callable[[Hashable], Any]], T]


class Lifetime(str, Enum):
    TRANSIENT = "transient"
    SINGLETON = "singleton"
    SCOPED = "scoped"


@dataclass(frozen=True)
class _Provider:
    factory: ProviderFactory[Any]
    lifetime: Lifetime


class Container:
    def __init__(self) -> None:
        self._providers: dict[Hashable, _Provider] = {}
        self._singletons: dict[Hashable, Any] = {}
        self._scoped_cache: ContextVar[dict[Hashable, Any] | None] = ContextVar(
            "skry_di_scoped_cache",
            default=None,
        )

    def register(
        self,
        token: Annotated[Hashable, Doc("Lookup token used to resolve a dependency.")],
        provider: Annotated[
            ProviderFactory[T],
            Doc("Factory callable that builds the dependency instance."),
        ],
        *,
        lifetime: Annotated[
            Lifetime,
            Doc("Lifecycle policy for produced instances."),
        ] = Lifetime.TRANSIENT,
        replace: Annotated[
            bool,
            Doc("Whether to replace an existing provider for this token."),
        ] = False,
    ) -> None:
        if token in self._providers and not replace:
            raise ProviderAlreadyRegisteredError(token)
        self._providers[token] = _Provider(
            factory=cast(ProviderFactory[Any], provider),
            lifetime=lifetime,
        )

    def resolve(
        self,
        token: Annotated[Hashable, Doc("Lookup token for the desired dependency.")],
    ) -> Any:
        provider = self._providers.get(token)
        if provider is None:
            raise ProviderNotFoundError(token)

        if provider.lifetime is Lifetime.TRANSIENT:
            return provider.factory(self.resolve)

        if provider.lifetime is Lifetime.SINGLETON:
            if token not in self._singletons:
                self._singletons[token] = provider.factory(self.resolve)
            return self._singletons[token]

        scoped_cache = self._scoped_cache.get()
        if scoped_cache is None:
            raise ScopeError("No active DI scope. Use `with container.scope():`.")

        if token not in scoped_cache:
            scoped_cache[token] = provider.factory(self.resolve)
        return scoped_cache[token]

    @contextmanager
    def scope(self) -> Iterator[None]:
        scope_token = self._scoped_cache.set({})
        try:
            yield
        finally:
            self._scoped_cache.reset(scope_token)
