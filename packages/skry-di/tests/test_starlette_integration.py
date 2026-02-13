from __future__ import annotations

from skry_di import Container, Lifetime
from skry_di.integrations.starlette import install_starlette, resolve_from_request
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient


class RequestService:
    pass


async def _handler(request: Request) -> JSONResponse:
    first = resolve_from_request(request, RequestService)
    second = resolve_from_request(request, RequestService)
    return JSONResponse({"same": first is second, "id": id(first)})


def test_starlette_request_scope_isolation() -> None:
    container = Container()
    container.register(
        RequestService,
        lambda _resolver: RequestService(),
        lifetime=Lifetime.SCOPED,
    )

    app = Starlette(routes=[Route("/", _handler)])
    install_starlette(app, container)

    with TestClient(app) as client:
        first = client.get("/").json()
        second = client.get("/").json()

    assert first["same"] is True
    assert second["same"] is True
    assert first["id"] != second["id"]
