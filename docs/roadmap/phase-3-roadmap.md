# Phase 3 Roadmap

## Objective

Phase 3 begins low-risk research automation on top of the completed Phase 2D workflow.

The goal is to add:

- Research Agent Gateway.
- Async job contract.
- MCP thin wrapper.
- SignalStrategy research lab.

Phase 3 remains research-first. It does not add broker order placement, live execution, AI trading authority, or public investment-advice positioning.

## Entry State

Phase 2D completed:

- Research brief.
- Persistent watchlist.
- Report comparison.
- Research templates.
- Report evidence labels.
- Safe retry flow.

Reference completion audit: `docs/roadmap/phase-2d-completion-audit.md`.

Reference adoption boundary: `docs/architecture/agent-gateway-and-strategy-lab.md`.

## Slice 1: Research Agent Gateway Foundation

Status: implemented and validated on 2026-06-19.

Purpose:

- Add the first machine-facing research API surface without exposing trading or secrets.
- Keep machine tokens separate from any future human session model.
- Start with read-only report access and scoped identity introspection.

Implemented surface:

- `agent_tokens` persistence model stores token hashes only.
- `GET /api/agent/v1/health` provides public gateway liveness.
- `GET /api/agent/v1/whoami` returns scoped identity for a valid agent token.
- `GET /api/agent/v1/reports` returns report list items for `R` scope tokens.
- `GET /api/agent/v1/reports/{report_id}` returns a report for `R` scope tokens.
- Missing/malformed tokens return `401`.
- Tokens without required read scope return `403`.
- Raw token values are not returned by gateway responses.

## Next Slices

### Slice 2: Agent Gateway Audit and Allowlists

Status: implemented and validated on 2026-06-19.

Implemented:

- Append-only agent audit log for success and denial events.
- Instrument allowlist enforcement for report detail reads.
- Instrument allowlist filtering for report list reads.
- Token expiry tests.
- In-process rate-limit guard for the local gateway process.

Deferred:

- Market allowlist enforcement remains deferred until report and job records carry an explicit market field.

### Slice 3: Async Job Contract

Planned:

- Durable job model for long-running research tasks.
- Submit/poll/progress/result contract.
- Reuse analysis runs where appropriate, but keep a stable agent-facing job API.
- Idempotency key support for writeful agent actions.

### Slice 4: MCP Thin Wrapper

Planned:

- MCP server wraps `/api/agent/v1` only.
- MCP must not read the database directly.
- MCP must not read local `.env` files or secret stores.
- Initial tools: `whoami`, `check_health`, `list_reports`, `get_report`, and later job operations.

### Slice 5: SignalStrategy Research Lab Plan

Planned:

- Define `SignalStrategy` dataframe contract.
- Define deterministic backtest contract.
- Define chart overlay and report-linked notes contract.
- Keep event-driven runtime strategies, paper execution, broker adapters, and live execution out of scope until separate risk controls are designed.

## Validation Targets

- Backend agent gateway tests pass.
- Existing analysis/report tests remain green.
- No secret values are displayed, logged, returned, or written into docs.
- Gateway routes do not expose trading scope.
- Phase 3 docs keep live execution out of scope.

## Validation Evidence

Slice 1 validation on 2026-06-19:

```bash
cd /home/yasin/workspace/TradingAgents/backend
. .venv/bin/activate
pytest -q tests/test_agent_gateway_api.py
```

Result:

```text
4 passed in 0.56s
```

Slice 2 validation on 2026-06-19:

```bash
cd /home/yasin/workspace/TradingAgents/backend
. .venv/bin/activate
pytest -q tests/test_agent_gateway_api.py
```

Result:

```text
8 passed in 0.74s
```
