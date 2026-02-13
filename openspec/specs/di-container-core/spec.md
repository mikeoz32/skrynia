# di-container-core Specification

## Purpose
TBD - created by archiving change add-di-container-package. Update Purpose after archive.
## Requirements
### Requirement: Register and resolve dependencies by explicit token
The DI container SHALL allow registering providers against explicit tokens and resolving instances by token in standalone Python runtime.

#### Scenario: Resolve a registered token
- **WHEN** a token is registered with a provider and the token is resolved
- **THEN** the container returns an instance produced by that provider

### Requirement: Support deterministic dependency lifetimes
The container MUST support singleton and transient lifetimes with deterministic behavior.

#### Scenario: Singleton lifetime returns shared instance
- **WHEN** a token is registered as singleton and resolved multiple times in the same container
- **THEN** the same instance is returned for each resolution

#### Scenario: Transient lifetime returns new instances
- **WHEN** a token is registered as transient and resolved multiple times
- **THEN** a new instance is returned for each resolution

### Requirement: Support scoped lifetimes
The container MUST support scoped dependencies that are reused within an active scope and isolated across different scopes.

#### Scenario: Scoped dependencies are reused within one scope
- **WHEN** a scoped token is resolved multiple times within the same active scope
- **THEN** the same scoped instance is returned

#### Scenario: Scoped dependencies are isolated across scopes
- **WHEN** a scoped token is resolved in two different scopes
- **THEN** each scope receives a different instance

### Requirement: Emit explicit errors for invalid resolution
The container SHALL raise explicit DI errors when resolution fails due to missing providers or invalid scope usage.

#### Scenario: Missing provider raises not-found error
- **WHEN** an unregistered token is resolved
- **THEN** resolution fails with a provider-not-found error that includes the token information

