from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated, Any, TypeVar, cast

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from typing_extensions import Doc

from skry_di.container import Container
from skry_di.exceptions import DIError
from skry_di.integrations.starlette import install_starlette, resolve_from_request

T = TypeVar("T")


class FastAPIResolutionError(RuntimeError):
    """Raised when FastAPI dependency resolution through the container fails."""


def install_fastapi(
    app: Annotated[FastAPI, Doc("Target FastAPI application instance.")],
    container: Annotated[
        Container,
        Doc("Configured container instance bound to the FastAPI app."),
    ],
) -> None:
    install_starlette(app, container)

    @app.exception_handler(FastAPIResolutionError)
    async def _handle_fastapi_resolution_error(
        _request: Request,
        exception: FastAPIResolutionError,
    ) -> JSONResponse:
        return JSONResponse(status_code=500, content={"detail": str(exception)})


def from_container(
    token: Annotated[Any, Doc("Token to resolve from the request container.")],
) -> Callable[[Request], Awaitable[T]]:
    async def _dependency(
        request: Annotated[Request, Doc("Current FastAPI request object.")],
    ) -> T:
        try:
            return cast(T, resolve_from_request(request, token))
        except DIError as error:
            raise FastAPIResolutionError(
                f"FastAPI DI resolution failed for token: {token!r}"
            ) from error

    return _dependency
