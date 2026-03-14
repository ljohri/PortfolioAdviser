# api-gateway

`api-gateway` is the SaaS-facing facade that exposes stable HTTP APIs to external clients.

## Scope (scaffold phase)

- Define public API surface and request routing boundaries
- Enforce service-edge concerns (authn/authz, quotas, versioning) later
- Defer business logic implementation until workflow validation

## Planned structure

- `tests/` for endpoint and contract tests
- gateway modules to be added in future iterations
