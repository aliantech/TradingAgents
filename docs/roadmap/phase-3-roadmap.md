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

Status: implemented and validated on 2026-06-19.

Implemented:

- `agent_jobs` durable persistence model for agent-facing jobs.
- `POST /api/agent/v1/jobs/research-analysis` submits a research analysis job with `A` scope.
- `GET /api/agent/v1/jobs/{job_id}` polls job status and progress with `R` scope.
- `GET /api/agent/v1/jobs/{job_id}/result` returns completed job results with `R` scope.
- Research analysis jobs reuse the existing analysis run/report service while keeping a stable agent-facing job API.
- `Idempotency-Key` replay returns the original job and analysis result for duplicate writeful submissions.
- Submit enforces token instrument allowlists before starting analysis.

Notes:

- This slice establishes the durable API contract. The current implementation completes the existing local analysis flow synchronously and records the completed job. A later worker slice can change the backend execution mode without changing the agent-facing contract.

### Slice 4: MCP Thin Wrapper

Status: implemented and validated on 2026-06-19.

Implemented:

- `backend/app/agent_mcp` provides a thin MCP JSON-RPC/tool wrapper.
- MCP tools forward to `/api/agent/v1` through an explicit Agent Gateway HTTP client.
- Implemented tools: `whoami`, `check_health`, `list_reports`, `get_report`, `submit_analysis`, `get_job`, and `get_job_result`.
- Tool calls preserve Agent Gateway token authentication and idempotency-key submission.
- Boundary tests assert the MCP wrapper does not import database access, dotenv helpers, environment variable reads, or local secret-file reads.
- Tool list excludes trading, broker, and order-placement tools.

Notes:

- The wrapper is intentionally thin. Authentication, scopes, rate limits, allowlists, and audit records remain owned by the Agent Gateway.

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

Slice 3 validation on 2026-06-19:

```bash
cd /home/yasin/workspace/TradingAgents/backend
. .venv/bin/activate
pytest -q tests/test_agent_gateway_api.py
```

Result:

```text
12 passed in 0.85s
```

Slice 4 validation on 2026-06-19:

```bash
cd /home/yasin/workspace/TradingAgents/backend
. .venv/bin/activate
pytest -q tests/test_agent_mcp_wrapper.py
```

Result:

```text
5 passed in 0.03s
```
