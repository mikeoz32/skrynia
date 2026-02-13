## 1. Workspace and Package Scaffolding

- [x] 1.1 Create new `packages/skry-di` package structure (`src/skry_di`, `tests`, `pyproject.toml`, `README.md`) and add it to workspace members.
- [x] 1.2 Configure package metadata and dependencies (core runtime + optional FastAPI/Starlette integration dependencies).
- [x] 1.3 Add lint/type/test configuration parity with existing workspace packages and ensure package discovery/import paths work.

## 2. Core DI Container Implementation

- [x] 2.1 Implement typed token/provider registration API with explicit lifetime selection (singleton, transient, scoped).
- [x] 2.2 Implement resolution pipeline with deterministic behavior, provider override policy, and explicit resolution errors.
- [x] 2.3 Implement scope manager using context-local state for async-safe scoped dependency reuse and isolation.
- [x] 2.4 Add unit tests for registration, singleton/transient/scoped lifetimes, missing-provider errors, and invalid scope usage.

## 3. Starlette Integration

- [x] 3.1 Implement Starlette integration setup for binding container access to app lifecycle.
- [x] 3.2 Implement middleware or equivalent request-lifecycle hook that creates and disposes one DI scope per request.
- [x] 3.3 Add integration tests validating request scope creation/disposal and request-scoped dependency isolation across concurrent requests.

## 4. FastAPI Integration

- [x] 4.1 Implement FastAPI dependency bridge helpers that resolve services from the container without patching FastAPI internals.
- [x] 4.2 Ensure FastAPI request handlers use active request scope semantics for scoped dependencies.
- [x] 4.3 Add integration tests for successful endpoint injection, missing-provider failure behavior, and per-request scope isolation.

## 5. Typed API Contracts and Documentation

- [x] 5.1 Apply modern type annotations across public API surface, including `Annotated[..., Doc("...")]` on public function/method parameters where applicable.
- [x] 5.2 Add static typing tests/checks to validate exported API contracts and generic container interfaces.
- [x] 5.3 Write usage documentation and examples for standalone usage, Starlette integration, and FastAPI integration.

## 6. Verification and Adoption Readiness

- [x] 6.1 Run full quality gates (`uv run pytest`, `uv run ruff check .`, `uv run mypy`) and resolve findings.
- [x] 6.2 Validate package can be consumed from workspace consumers with minimal bootstrap.
- [x] 6.3 Finalize migration notes and rollout guidance for opt-in adoption by services/modules.
