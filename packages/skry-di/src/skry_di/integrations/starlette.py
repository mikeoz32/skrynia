from __future__ import annotations

from typing import Annotated, Any, TypeVar

from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from typing_extensions import Doc

from skry_di.container import Container
from skry_di.exceptions import ScopeError

T = TypeVar("T")
_CONTAINER_STATE_KEY = "di_container"


class ContainerMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: Any,
        *,
        container: Annotated[
            Container,
            Doc("Container used for request-scoped dependency resolution."),
        ],
    ) -> None:
        super().__init__(app)
        self._container = container

    async def dispatch(self, request: Request, call_next: Any) -> Any:
        with self._container.scope():
            return await call_next(request)


def install_starlette(
    app: Annotated[Starlette, Doc("Target Starlette application instance.")],
    container: Annotated[
        Container,
        Doc("Configured container instance bound to the application."),
    ],
) -> None:
    setattr(app.state, _CONTAINER_STATE_KEY, container)
    app.add_middleware(ContainerMiddleware, container=container)


def get_container_from_request(
    request: Annotated[Request, Doc("Current Starlette request object.")],
) -> Container:
    container = getattr(request.app.state, _CONTAINER_STATE_KEY, None)
    if not isinstance(container, Container):
        raise ScopeError("Container is not attached to the request application.")
    return container


def resolve_from_request(
    request: Annotated[Request, Doc("Current Starlette request object.")],
    token: Annotated[Any, Doc("Token to resolve from the attached container.")],
) -> Any:
    return get_container_from_request(request).resolve(token)

