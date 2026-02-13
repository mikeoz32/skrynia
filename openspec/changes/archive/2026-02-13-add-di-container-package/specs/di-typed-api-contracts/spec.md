## ADDED Requirements

### Requirement: Public APIs use modern type annotations
Public container and integration APIs MUST declare explicit Python type annotations for parameters and return values.

#### Scenario: Public API signatures are fully typed
- **WHEN** the package public APIs are inspected
- **THEN** exported functions and methods include concrete parameter and return type annotations

### Requirement: Public function and method parameters include Annotated Doc metadata
Public APIs SHALL use `Annotated[..., Doc("...")]` on parameters where argument purpose must be documented.

#### Scenario: Parameter documentation is embedded in signature metadata
- **WHEN** a user inspects supported public API signatures
- **THEN** documented parameters include `Annotated` with `Doc` metadata describing intent and usage

### Requirement: Type contracts remain compatible with static type checking
Type annotations MUST be valid for static type checking under project type-checking rules.

#### Scenario: Type checker accepts public API contracts
- **WHEN** static type checking runs for the package
- **THEN** type checker passes for exported API signatures and generic DI contracts
