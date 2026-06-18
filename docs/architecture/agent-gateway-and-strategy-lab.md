# Agent Gateway and Strategy Lab Adoption Plan

## Status

Status: Active adoption boundary
Last Reviewed: 2026-06-19
Owner: Yasin

## Purpose

This document records how the AQuantLens US/options branch may learn from `github.com/brokermr810/QuantDinger` without importing its product shell or weakening the branch safety boundary.

QuantDinger is useful as an architectural reference for agent access, MCP wrapping, paper-only defaults, asynchronous jobs, strategy development contracts, and broker adapter boundaries. It is not a drop-in dependency for this workspace.

## Decision

Use QuantDinger as a capability reference only.

Do not merge the repository, migrate to Flask/Vue, or absorb its SaaS, billing, referral, membership, USDT payment, community, grid bot, martingale bot, crypto exchange runtime, or live trading product surface.

AQuantLens keeps its own stack:

- FastAPI backend.
- React/Vite/TypeScript frontend.
- SQLAlchemy persistence.
- Database-backed runtime settings.
- TradingAgents-centered research workflow.
- Chinese-first reports.
- U.S. equities, SPX/SPY/QQQ, and selected U.S. options.

## Reference Capabilities

QuantDinger capabilities that are worth adapting into AQuantLens patterns:

- Agent Gateway with machine tokens separate from human sessions.
- Token scopes, market allowlists, instrument allowlists, expiry, rate limits, and audit logs.
- MCP server as a thin wrapper over the Agent Gateway, not as a direct database or service bypass.
- Paper-only default for all agent-originated trading-class capabilities.
- Server-side kill switch before any live trading path can execute.
- Append-only audit trail for agent calls, denials, and paper/live order intents.
- Idempotency keys for writeful agent actions.
- Asynchronous job submission for long-running analysis, backtests, and experiments.
- Strategy development distinction between dataframe signal research and event-driven runtime strategies.
- Stable execution contracts such as order intent, fill snapshot, position snapshot, and broker adapter interface.
- Offline contract fixtures and security/permission regression tests for agent and broker behavior.

## AQuantLens Scope Mapping

### Phase 2D

Phase 2D remains research-only.

Allowed:

- Continue improving research brief, report comparison, research templates, and Chinese report quality.
- Document future Agent Gateway and Strategy Lab boundaries.

Not allowed:

- Broker order placement.
- AI trading authority.
- Live execution.
- MCP tools that can place orders or change broker credentials.

### Phase 3 Candidate: Research Agent Gateway

The first AQuantLens Agent Gateway should expose only research and read-oriented capabilities:

- `GET /api/agent/v1/health`
- `GET /api/agent/v1/market-context/{symbol}`
- `GET /api/agent/v1/options-summary/{symbol}`
- `GET /api/agent/v1/reports`
- `GET /api/agent/v1/reports/{report_id}`
- `GET /api/agent/v1/analysis-runs`
- `POST /api/agent/v1/analysis-runs`
- `GET /api/agent/v1/jobs/{job_id}`

Initial scopes:

- `R`: read market context, option summaries, reports, and run metadata.
- `A`: submit TradingAgents research analysis.

Do not introduce `T` trading scope in the first gateway implementation.

### Phase 3 Candidate: MCP Thin Wrapper

Status: first thin wrapper implemented in Phase 3 Slice 4.

The MCP server, if added, must call `/api/agent/v1` and rely on the Agent Gateway for authentication, scope checks, rate limits, and audit logging.

Implemented MCP wrapper tools are limited to:

- `whoami`
- `check_health`
- `list_reports`
- `get_report`
- `submit_analysis`
- `get_job`
- `get_job_result`

Deferred research tools:

- `get_market_context`
- `get_options_summary`
- `list_analysis_runs`

MCP must not:

- Read the database directly.
- Read local `.env` or secret stores.
- Accept broker credentials.
- Expose live trading or broker account mutation.

### Phase 4 Candidate: Strategy Lab

Use a staged strategy model:

- `SignalStrategy`: dataframe-based indicator and signal research.
- `RuntimeStrategy`: event-driven strategy for paper-only runtime behavior.

Start with `SignalStrategy` only. It should support deterministic backtests, chart overlays, signal review, and report-linked research notes.

`RuntimeStrategy` should wait until AQuantLens has:

- Paper execution model.
- Risk guard.
- Position sizing rules.
- Audit log.
- Human confirmation path.
- Broker adapter contracts.

## Safety Boundary

All future trading-class capabilities must pass through this sequence:

```text
Research Signal
-> Strategy Intent
-> RiskGuard
-> Position Sizing
-> Human Confirmation or Explicit Auto-Paper Gate
-> PaperExecutionAdapter
-> AuditLog
```

Live broker execution remains out of scope until a separate decision explicitly approves it.

If live execution is later approved, it must add:

- `T` scope with paper-only default.
- Server-side live trading kill switch.
- Account allowlist.
- Instrument allowlist.
- Max notional per order and per day.
- Order idempotency.
- Agent-originated order tagging.
- Emergency revoke and cancel workflow.
- Dedicated live broker tests with offline fixtures first.

## Implementation Order

Recommended sequence:

1. Finish Phase 2D research workflow slices.
2. Add an Agent Gateway architecture spec and database schema plan.
3. Implement read-only/research Agent Gateway tokens and audit log.
4. Add async job contract for analysis runs, then reuse it for future backtests.
5. Add MCP wrapper over Agent Gateway read/research endpoints.
6. Add `SignalStrategy` research/backtest planning.
7. Add paper-only execution contracts and RiskGuard.
8. Consider live broker adapters only after paper trading is validated.

## Test Themes to Borrow

Future tests should cover:

- Missing, malformed, expired, revoked, and insufficient-scope agent tokens.
- Market and instrument allowlist enforcement.
- Agent audit records for success, denial, and rate limiting.
- Idempotency-key replay for writeful endpoints.
- MCP tool responses redacting secrets and staying within scoped APIs.
- Hosted/shared deployment guard that forbids trading scope.
- Backtest strict-mode semantics.
- Broker adapter contract fixtures before any live network call.
- Paper-only enforcement for every agent-originated trading path.

## License Note

QuantDinger is published under Apache-2.0. Architectural ideas may be referenced freely. If AQuantLens copies code or substantial text in the future, preserve required license and notice attribution in the copied files and project documentation.
