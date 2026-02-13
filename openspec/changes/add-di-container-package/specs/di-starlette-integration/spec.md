## ADDED Requirements

### Requirement: Attach container integration at Starlette application level
The Starlette integration MUST provide an application-level setup entrypoint that binds the DI container to app lifecycle.

#### Scenario: App is configured with DI integration
- **WHEN** Starlette app startup executes with DI integration configured
- **THEN** the application has access to the configured container for request handling

### Requirement: Manage per-request DI scope in Starlette
The Starlette integration SHALL create and dispose a request scope for each HTTP request.

#### Scenario: Request scope is created and disposed
- **WHEN** an HTTP request enters and exits the Starlette app
- **THEN** one request scope is created before handler execution and disposed after response completion

### Requirement: Expose request-level container access
The integration MUST expose access to request-scoped resolution from request context without coupling business code to framework internals.

#### Scenario: Handler resolves request-scoped dependency
- **WHEN** a Starlette route handler requests a DI-managed dependency during an active request
- **THEN** the dependency is resolved from the active request scope
