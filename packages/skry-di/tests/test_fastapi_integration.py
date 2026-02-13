from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from skry_di import Container, Lifetime
from skry_di.integrations.fastapi import from_container, install_fastapi


class RequestService:
    pass


class MissingService:
    pass


app = FastAPI()
container = Container()
container.register(
    RequestService,
    lambda _resolver: RequestService(),
    lifetime=Lifetime.SCOPED,
)
install_fastapi(app, container)


@app.get("/id")
def get_id(
    first: Annotated[RequestService, Depends(from_container(RequestService))],
    second: Annotated[RequestService, Depends(from_container(RequestService))],
) -> dict[str, int | bool]:
    return {"same": first is second, "id": id(first)}


def test_fastapi_integration_scoping() -> None:
    with TestClient(app) as client:
        first = client.get("/id").json()
        second = client.get("/id").json()

    assert first["same"] is True
    assert second["same"] is True
    assert first["id"] != second["id"]


def test_fastapi_integration_missing_provider_reports_token() -> None:
    missing_app = FastAPI()
    install_fastapi(missing_app, Container())

    @missing_app.get("/missing")
    def missing_endpoint(
        dep: Annotated[MissingService, Depends(from_container(MissingService))],
    ) -> dict[str, bool]:
        return {"ok": dep is not None}

    with TestClient(missing_app, raise_server_exceptions=False) as client:
        response = client.get("/missing")

    assert response.status_code == 500
    assert "MissingService" in response.json()["detail"]
