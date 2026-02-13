## Why

The workspace currently lacks a reusable dependency injection foundation, which forces ad-hoc wiring and framework-coupled patterns. We need a shared DI package now to support consistent service composition across standalone Python code and ASGI applications.

## What Changes

- Add a new workspace package for DI (standalone-first) with explicit service registration and resolution APIs.
- Introduce lifecycle/scoping support suitable for application and request boundaries (for example singleton, transient, and request-scoped behavior).
- Add Starlette integration for request lifecycle binding and container access in app/request context.
- Add FastAPI integration that bridges container resolution into FastAPI dependency patterns.
- Ensure public APIs are fully typed using modern Python type annotations, including `Annotated[..., Doc(...)]` for function/method parameters.
- Add tests and usage docs for standalone usage and both framework integrations.

## Capabilities

### New Capabilities
- `di-container-core`: Typed DI container primitives for registration, resolution, lifetimes/scopes, and error handling.
- `di-starlette-integration`: Starlette hooks/utilities that attach container scope to app/request lifecycle.
- `di-fastapi-integration`: FastAPI-facing integration layer for resolving container-managed dependencies in endpoints.
- `di-typed-api-contracts`: Public API requirements for modern typing, including `Annotated` + `Doc` parameter metadata.

### Modified Capabilities
- None.

## Impact

- New package added under `packages/` in the `uv` workspace (name to be finalized during design/specs).
- New test modules for container core and integration behavior.
- Optional framework dependencies (`starlette`, `fastapi`) introduced for integration capabilities.
- Developer documentation/examples expanded to cover standalone and ASGI framework usage patterns.
