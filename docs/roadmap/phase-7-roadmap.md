# Phase 7 Roadmap

## Objective

Phase 7 reconnects AQuantLens US/options to real TradingAgents research execution.

The immediate goal is to replace the current failed/no-report analysis placeholder path with a durable, observable research execution path that can produce Chinese-first reports from the underlying TradingAgents framework.

This phase is not a live-trading phase. It does not add broker order placement, broker credentials, AI-directed live trading, trading-scope MCP tools, or paper-to-live promotion.

## Entry State

Phase 6 completed paper-only workflow hardening:

- Strategy Lab Candidate-to-Paper browser smoke coverage.
- Paper account summary API.
- Paper PnL snapshot API using explicit caller-provided reference prices.
- Strategy Lab paper risk dashboard.
- Completion audit: `docs/roadmap/phase-6-completion-audit.md`.

Known product gap:

- The checked-in analysis endpoint no longer emits sample or mock reports.
- Until the real TradingAgents execution chain is connected, analysis runs are persisted as failed/no-report instead of writing placeholder report content.

## Design Principles

- Real research execution before new trading behavior.
- Keep the existing analysis persistence and report schema as the product boundary.
- Make execution observable: status, progress, errors, model/provider metadata, and report id must be inspectable.
- Prefer deterministic adapters and test fixtures before calling external model providers in verification.
- Never read, print, store, or expose secrets in logs, reports, tests, or docs.
- Live broker execution remains out of scope.

## Phase 7 Slices

### Slice 1: Phase 7 Roadmap and Execution Boundary

Status: implemented and verified.

Goal:

- Define the real-research-execution phase and safety boundary.

Deliverables:

- Phase 7 roadmap.
- Slice 1 implementation plan.
- Project status update marking Phase 7 as research execution integration.
- Yasin Brain log entry recording that live execution remains out of scope.

Verification:

- Documentation does not authorize live execution.
- Documentation keeps broker credentials, broker account mutation, trading-scope MCP tools, and paper-to-live promotion out of scope.
- Project status points to Phase 7 research execution integration.

### Slice 2: TradingAgents Execution Adapter Contract

Status: implemented and verified.

Goal:

- Define a backend adapter interface for invoking TradingAgents research runs from the FastAPI analysis service.

Expected coverage:

- Input contract maps existing analysis request fields to TradingAgents config.
- Output contract maps TradingAgents results to the existing report schema.
- Progress events are normalized to existing analysis status events.
- Errors are captured without leaking secrets or raw provider payloads.

Verification:

- Unit tests cover successful adapter output mapping.
- Unit tests cover provider/model/runtime error mapping.
- Tests prove no broker/trading execution surface is introduced.

Implemented:

- `backend/app/analysis/tradingagents_adapter.py`.
- `backend/tests/test_tradingagents_adapter.py`.
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-7-slice-2-adapter-contract.md`.

Verification completed:

- Local compile check passed for the adapter and adapter tests.
- Ubuntu temp-copy focused regression passed: 13 tests.
- Ubuntu temp-copy full backend regression passed: 229 tests.

### Slice 3: Deterministic Research Runner Fixture

Status: implemented and focused-verified.

Goal:

- Add a deterministic local research runner fixture that exercises the real adapter boundary without external model calls.

Expected coverage:

- Analysis run transitions from queued/running to completed.
- Report row is created through the existing repository path.
- Chinese-first report fields are populated from deterministic fixture output.
- Failed fixture path produces failed/no-report state with clear error details.

Verification:

- Backend API tests cover successful completed analysis and persisted report.
- Backend API tests cover deterministic failure.
- Existing failed/no-report safety behavior remains available when execution fails.

Implemented:

- `backend/app/analysis/deterministic_runner.py`.
- `backend/app/analysis/service.py` now routes analysis execution through the deterministic fixture and Slice 2 adapter contract.
- `backend/tests/test_analysis_api_persistence.py`.
- `backend/tests/test_analysis_retry_api.py`.
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-7-slice-3-deterministic-runner.md`.

Verification completed:

- Local compile check passed for the service, deterministic runner, and updated tests.
- Ubuntu temp-copy focused regression passed: 16 tests.
- Ubuntu temp-copy full backend regression passed: 230 tests.

### Slice 4: Real TradingAgents Runner Integration

Status: planned.

Goal:

- Connect the adapter to the actual local TradingAgents execution chain behind an explicit runtime gate.

Expected coverage:

- Runtime gate prevents accidental provider calls in tests.
- Provider/model settings are read from the existing settings/runtime boundary.
- Analysis progress is persisted while the run executes.
- Output is transformed into the existing report contract.

Verification:

- Tests use mocked TradingAgents execution, not live providers.
- Smoke command is documented for manual local/Ubuntu verification when credentials are intentionally configured.
- Safety grep proves no secrets are read or printed by tests/docs.

### Slice 5: Analysis Run Observability UI

Status: planned.

Goal:

- Improve frontend visibility for real research execution progress and failure reasons.

Expected coverage:

- Progress timeline.
- Current execution state.
- Report link when complete.
- Clear failed/no-report state.
- Retry affordance remains explicit and user-controlled.

Verification:

- Frontend build passes.
- UI tests or browser smoke cover completed and failed states with mocked API responses.
- UI copy remains research-only and does not imply trading authority.

### Slice 6: Phase 7 Completion Audit

Status: planned.

Goal:

- Audit Phase 7 after implementation and record residual risks.

Verification:

- Focused backend analysis execution tests pass.
- Full backend regression passes.
- Frontend build passes.
- Browser smoke passes when UI changes.
- Safety grep confirms no broker SDK, broker credentials, live order methods, trading-scope MCP tools, or paper-to-live controls were introduced.
- Project docs and Yasin Brain record completion and remaining live-execution boundary.

## Explicit Non-Goals

- Live broker order placement.
- Broker credential storage or mutation.
- Broker account balance sync.
- Broker order status sync.
- AI-direct live trading authority.
- Trading-scope MCP tools that can reach a broker.
- Live-trading UI controls.
- Automatic paper-to-live promotion.
- Production-grade distributed job orchestration.
- Public multi-user SaaS execution.

## Completion Criteria

Phase 7 is complete only when:

- The analysis API can complete a deterministic research execution and persist a report.
- The real TradingAgents runner is connected behind an explicit runtime gate.
- Analysis progress, completion, failure, and report id are observable.
- Focused analysis tests, backend regression, frontend build, and relevant browser smoke pass.
- Safety grep confirms no live-execution boundary violations.
- Project docs and Yasin Brain record that live execution remains out of scope.
