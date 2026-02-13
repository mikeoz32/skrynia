# skry-di

`skry-di` is a lightweight typed DI container package for standalone Python projects,
with optional Starlette and FastAPI integrations.

## Features

- Explicit, typed registration and resolution API
- Deterministic lifetimes: `transient`, `singleton`, `scoped`
- Request-scope integration for Starlette and FastAPI
- Public API signatures documented with `Annotated[..., Doc(...)]`

## Installation

From this workspace root:

```bash
uv sync --all-packages --all-groups
```

As a dependency:

```bash
uv add skry-di
```

Optional integrations:

```bash
uv add "skry-di[starlette]"
uv add "skry-di[fastapi]"
```

## Standalone Usage

```python
from skry_di import Container, Lifetime


class Settings:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn


container = Container()
container.register(
    Settings,
    lambda _resolve: Settings(dsn="sqlite:///app.db"),
    lifetime=Lifetime.SINGLETON,
)

settings = container.resolve(Settings)
```

## Starlette Integration

```python
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from skry_di import Container, Lifetime
from skry_di.integrations.starlette import install_starlette, resolve_from_request


class RequestService:
    pass


async def homepage(request: Request) -> JSONResponse:
    service = resolve_from_request(request, RequestService)
    return JSONResponse({"service_id": id(service)})


container = Container()
container.register(
    RequestService,
    lambda _resolve: RequestService(),
    lifetime=Lifetime.SCOPED,
)

app = Starlette(routes=[Route("/", homepage)])
install_starlette(app, container)
```

## FastAPI Integration

```python
from typing import Annotated

from fastapi import Depends, FastAPI

from skry_di import Container, Lifetime
from skry_di.integrations.fastapi import from_container, install_fastapi


class RequestService:
    pass


container = Container()
container.register(
    RequestService,
    lambda _resolve: RequestService(),
    lifetime=Lifetime.SCOPED,
)

app = FastAPI()
install_fastapi(app, container)


@app.get("/service")
def get_service(
    service: Annotated[RequestService, Depends(from_container(RequestService))],
) -> dict[str, int]:
    return {"service_id": id(service)}
```

## Migration Notes

- `skry-di` is additive and opt-in. Existing services are unchanged until they import
  and install it.
- Start by wiring container setup in application bootstrap, then migrate one module at
  a time.
- For web apps, prefer request-scoped services for request-local state and singleton
  services for shared stateless resources.
