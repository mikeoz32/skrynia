from __future__ import annotations

import pytest
from skry_di import (
    Container,
    Lifetime,
    ProviderAlreadyRegisteredError,
    ProviderNotFoundError,
    ScopeError,
)


class Service:
    pass


class RequestService:
    pass


class Repository:
    def __init__(self, service: Service) -> None:
        self.service = service


class UseCase:
    def __init__(self, repository: Repository) -> None:
        self.repository = repository


def test_transient_returns_new_instance() -> None:
    container = Container()
    container.register(
        Service,
        lambda _resolver: Service(),
        lifetime=Lifetime.TRANSIENT,
    )

    first = container.resolve(Service)
    second = container.resolve(Service)

    assert first is not second


def test_singleton_returns_same_instance() -> None:
    container = Container()
    container.register(
        Service,
        lambda _resolver: Service(),
        lifetime=Lifetime.SINGLETON,
    )

    first = container.resolve(Service)
    second = container.resolve(Service)

    assert first is second


def test_scoped_resolution_requires_scope() -> None:
    container = Container()
    container.register(
        RequestService,
        lambda _resolver: RequestService(),
        lifetime=Lifetime.SCOPED,
    )

    with pytest.raises(ScopeError):
        container.resolve(RequestService)


def test_scoped_resolution_reuses_in_scope_and_isolates_between_scopes() -> None:
    container = Container()
    container.register(
        RequestService,
        lambda _resolver: RequestService(),
        lifetime=Lifetime.SCOPED,
    )

    with container.scope():
        first = container.resolve(RequestService)
        second = container.resolve(RequestService)
        assert first is second

    with container.scope():
        third = container.resolve(RequestService)

    assert third is not first


def test_missing_provider_raises() -> None:
    container = Container()

    with pytest.raises(ProviderNotFoundError):
        container.resolve(Service)


def test_register_duplicate_raises_without_replace() -> None:
    container = Container()
    container.register(Service, lambda _resolver: Service())

    with pytest.raises(ProviderAlreadyRegisteredError):
        container.register(Service, lambda _resolver: Service())


def test_register_replace_overwrites_provider() -> None:
    class InitialService:
        pass

    class ReplacementService:
        pass

    container = Container()
    container.register(Service, lambda _resolver: InitialService())
    container.register(
        Service,
        lambda _resolver: ReplacementService(),
        replace=True,
    )

    resolved = container.resolve(Service)
    assert isinstance(resolved, ReplacementService)


def test_nested_dependency_tree_resolves_transitively() -> None:
    container = Container()
    container.register(Service, lambda _resolve: Service(), lifetime=Lifetime.SINGLETON)
    container.register(
        Repository,
        lambda resolve: Repository(resolve(Service)),
        lifetime=Lifetime.TRANSIENT,
    )
    container.register(
        UseCase,
        lambda resolve: UseCase(resolve(Repository)),
        lifetime=Lifetime.TRANSIENT,
    )

    first = container.resolve(UseCase)
    second = container.resolve(UseCase)

    assert isinstance(first, UseCase)
    assert isinstance(second, UseCase)
    assert first is not second
    assert first.repository is not second.repository
    assert first.repository.service is second.repository.service


def test_nested_scoped_dependency_tree_reuses_in_scope() -> None:
    container = Container()
    container.register(Service, lambda _resolve: Service(), lifetime=Lifetime.SINGLETON)
    container.register(
        Repository,
        lambda resolve: Repository(resolve(Service)),
        lifetime=Lifetime.SCOPED,
    )
    container.register(
        UseCase,
        lambda resolve: UseCase(resolve(Repository)),
        lifetime=Lifetime.SCOPED,
    )

    with container.scope():
        first = container.resolve(UseCase)
        second = container.resolve(UseCase)
        assert first is second
        assert first.repository is second.repository

    with container.scope():
        third = container.resolve(UseCase)

    assert third is not first
    assert third.repository is not first.repository
    assert third.repository.service is first.repository.service


def test_nested_dependency_tree_missing_leaf_provider_raises() -> None:
    container = Container()
    container.register(
        Repository,
        lambda resolve: Repository(resolve(Service)),
        lifetime=Lifetime.TRANSIENT,
    )
    container.register(
        UseCase,
        lambda resolve: UseCase(resolve(Repository)),
        lifetime=Lifetime.TRANSIENT,
    )

    with pytest.raises(ProviderNotFoundError):
        container.resolve(UseCase)
