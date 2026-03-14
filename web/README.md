# Web Layer Constraints

`web/` is a consumer application layer in this monorepo. It must follow these architectural constraints:

- `datalake` is the source of truth.
- `mcp-stocklake` is the OpenClaw-facing tool service.
- `api-gateway` is the public SaaS-facing API.
- `analytics` and `screener` are separate derived-data services.
- `web` consumes `api-gateway`, not `datalake` directly.
- Business logic lives in service layers, not route handlers.
- MCP tools must wrap existing service-layer methods.
- Test coverage is mandatory at unit, integration, and E2E levels.
- OpenClaw skills provide concise tool-use guidance only.
- Keep TimescaleDB migration concerns localized to storage layers and migrations.

## Practical implications for `web`

- Treat `api-gateway` contracts as the integration surface.
- Do not add direct database access or datalake-specific client code in `web`.
- Keep `web` focused on presentation, orchestration, and UX concerns.
