## Context

The change introduces a new dependency-injection package in a multi-package `uv` workspace where reusable service wiring is currently missing. The package must work as a standalone library and also integrate cleanly with Starlette and FastAPI request lifecycles. Constraints include modern typing expectations (including `Annotated[..., Doc(...)]` on public function/method parameters), low coupling between core container logic and framework adapters, and maintainable extension points for future frameworks.

## Goals / Non-Goals

**Goals:**
- Provide a standalone DI container package with explicit registration and resolution APIs.
- Support predictable lifetimes/scopes: singleton, transient, and request-scoped dependencies.
- Add Starlette integration that creates and disposes request scope per request.
- Add FastAPI integration that resolves container-managed dependencies via FastAPI dependency patterns.
- Keep public APIs strongly typed and documented using `Annotated` + `Doc` metadata.

**Non-Goals:**
- Replace FastAPI built-in DI semantics globally.
- Implement auto-discovery/magic registration via module scanning.
- Provide advanced compile-time graph optimizations in first release.
- Add framework integrations beyond Starlette/FastAPI in this change.

## Decisions

1. Create a new standalone package `packages/skry-di` with separated modules:
- `core/` for container, provider registry, scopes, exceptions.
- `integrations/starlette.py` and `integrations/fastapi.py` as thin adapters.
Rationale: clean boundaries and SOLID adherence; framework code depends on core, not vice versa.
Alternatives considered:
- Add DI inside `skry-sqla`: rejected (wrong domain ownership).
- Single flat module: rejected due to growing complexity and weaker extension boundaries.

2. Use explicit provider registration API with typed callables/factories.
Rationale: explicit wiring is easier to reason about, test, and document than implicit reflection-heavy injection.
Alternatives considered:
- Constructor signature auto-wiring only: rejected for hidden behavior and ambiguous resolution paths.

3. Model request scoping via context-local scope state (`contextvars`) with adapter-managed enter/exit.
Rationale: works for async request concurrency without leaking scoped instances across requests.
Alternatives considered:
- Thread-local scope storage: rejected for async correctness.

4. FastAPI integration will expose helper dependency factories (for example, `FromContainer[T]` patterns) rather than monkey-patching internals.
Rationale: minimizes coupling to FastAPI internal changes and remains explicit to endpoint authors.
Alternatives considered:
- Overriding dependency resolution pipeline: rejected due to fragility.

5. Public API signatures will include `Annotated[..., Doc("...")]` for parameters where runtime/docs clarity is needed.
Rationale: aligns with project typing requirements and self-documenting API design.
Alternatives considered:
- Docstrings only: rejected as less structured for tooling.

## Risks / Trade-offs

- [Risk] Request scope cleanup bugs may leak objects between requests → Mitigation: enforce adapter-managed context managers and add concurrency tests.
- [Risk] Ambiguous provider registrations (same token, different lifetimes) → Mitigation: deterministic override rules + explicit error classes.
- [Risk] Framework integration drift with upstream FastAPI/Starlette updates → Mitigation: keep adapters thin and integration tests pinned to supported versions.
- [Trade-off] Explicit registration increases boilerplate compared to magic DI → Mitigation: helper registration utilities while preserving explicitness.

## Migration Plan

1. Scaffold `packages/skry-di` as a new workspace member with strict typing/lint/test config parity.
2. Implement core container + provider + scope primitives and unit tests.
3. Implement Starlette adapter and request-lifecycle tests.
4. Implement FastAPI adapter and endpoint dependency tests.
5. Add usage docs/examples for standalone, Starlette, and FastAPI.
6. Rollout: opt-in package adoption per service/module.

Rollback strategy:
- Since this is additive, rollback is removing package adoption points and excluding the package from workspace dependencies.

## Open Questions

- Should the default registration policy allow overrides by default or require explicit `replace=True`?
- Do we expose a decorator-based registration helper in v1, or keep API purely imperative?
- Should request-scoped resolution outside an active request context raise immediately or fallback to transient behavior?
