from importlib.metadata import PackageNotFoundError, version

from .container import Container, Lifetime
from .exceptions import (
    DIError,
    ProviderAlreadyRegisteredError,
    ProviderNotFoundError,
    ScopeError,
)
from .integrations.fastapi import (
    FastAPIResolutionError,
    from_container,
    install_fastapi,
)
from .integrations.starlette import (
    ContainerMiddleware,
    get_container_from_request,
    install_starlette,
    resolve_from_request,
)

try:
    __version__ = version("skry-di")
except PackageNotFoundError:
    __version__ = "0.1.0"

__all__ = [
    "__version__",
    "Container",
    "ContainerMiddleware",
    "DIError",
    "FastAPIResolutionError",
    "Lifetime",
    "ProviderAlreadyRegisteredError",
    "ProviderNotFoundError",
    "ScopeError",
    "from_container",
    "get_container_from_request",
    "install_fastapi",
    "install_starlette",
    "resolve_from_request",
]
