## ADDED Requirements

### Requirement: Provide FastAPI dependency bridge to container
The FastAPI integration SHALL provide dependency helper APIs that allow endpoint functions to resolve DI-managed services.

#### Scenario: Endpoint receives container-managed dependency
- **WHEN** a FastAPI endpoint declares a supported DI helper dependency
- **THEN** FastAPI injects a value resolved from the container

### Requirement: Respect request scope in FastAPI endpoints
The FastAPI integration MUST resolve request-scoped services within the active request scope and isolate them between requests.

#### Scenario: Request-scoped service is stable within one request
- **WHEN** the same request-scoped token is resolved multiple times during one FastAPI request
- **THEN** each resolution returns the same request-scoped instance

#### Scenario: Request-scoped service is isolated across requests
- **WHEN** two separate FastAPI requests resolve the same request-scoped token
- **THEN** each request receives a different instance

### Requirement: Preserve explicit failure semantics for invalid DI resolution
The FastAPI integration SHALL surface DI resolution failures as explicit runtime errors suitable for API error handling.

#### Scenario: Endpoint resolution fails for missing provider
- **WHEN** an endpoint requests a token with no registered provider
- **THEN** the request fails with an integration-level error that identifies the missing token
