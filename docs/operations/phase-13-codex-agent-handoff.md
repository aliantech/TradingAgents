# Phase 13 Codex Agent Handoff

Status: Active handoff
Last Reviewed: 2026-07-01
Owner: Yasin

## Purpose

Bind the Codex `Research-Runner Agent` and `Report-Review Agent` roles to the current Phase 13 state.

This handoff is operational only. It does not create a backend service, autonomous scheduler, MCP tool, trading tool, or live-execution path.

## Current State

- Branch: `aquantlens-us`.
- Current clean Ubuntu mirror: `/home/yasin/workspace/TradingAgents-current`, kept fast-forwarded to `origin/aquantlens-us`.
- Legacy Ubuntu workspace: `/home/yasin/workspace/TradingAgents` is behind `origin/aquantlens-us` and contains unrelated local changes; do not reset, pull, or use it as the current sync target without a separate cleanup decision.
- Current target: `QQQ 2026-06-18 etf require-option-chain-context`.
- Readiness state: QQQ passed the option-chain gate in no-provider preflight.
- Blocking state: the current execution environment blocked the real provider-backed run because it would send runtime context and research input to an external LLM/provider.
- Evidence: `docs/operations/phase-13-qqq-gated-preflight.md`.

## Clean Mirror Regression

The Phase 13 focused regression slice passed from `/home/yasin/workspace/TradingAgents-current`:

```bash
PYTHONPATH=backend /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest \
  backend/tests/test_analysis_cli_real_runner_smoke.py \
  backend/tests/test_phase8_real_runner_smoke_script.py \
  backend/tests/test_analysis_option_chain_context.py \
  backend/tests/test_tradingagents_runner.py \
  backend/tests/test_report_quality.py \
  -q
```

Result:

```text
25 passed in 0.41s
```

The backend full regression also passed after isolating the Phase 1 empty-context test from live Finance Data Hub data:

```bash
cd /home/yasin/workspace/TradingAgents-current/backend
PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q --tb=short
```

Result:

```text
225 passed in 8.51s
```

The frontend production build also passed from the clean mirror after installing dependencies with `npm ci`:

```bash
cd /home/yasin/workspace/TradingAgents-current/frontend
npm run build
```

Result:

```text
tsc -b && vite build
1928 modules transformed
built in 476ms
```

The mocked Playwright smoke suite also passed from the clean mirror:

```bash
cd /home/yasin/workspace/TradingAgents-current/frontend
npm run e2e:paper
```

Result:

```text
4 passed (9.1s)
```

## Research-Runner Agent Assignment

### Objective

Run exactly one guarded QQQ provider-backed smoke only in an approved environment.

### Required Inputs

- Symbol: `QQQ`.
- Analysis date: `2026-06-18`.
- Asset type: `etf`.
- Gate: `require-option-chain-context`.
- Runtime mode: `real-tradingagents`.
- Runtime database: the approved TradingAgents runtime database for this branch.
- Working directory: use `/home/yasin/workspace/TradingAgents-current` unless an operator explicitly chooses another clean checkout.

### Command Template

```bash
AQUANTLENS_DATABASE_URL=sqlite:////home/yasin/workspace/TradingAgents/backend/aquantlens_us.db \
AQUANTLENS_TRADINGAGENTS_RUNNER_MODE=real-tradingagents \
PATH=/home/yasin/workspace/TradingAgents/backend/.venv/bin:$PATH \
scripts/phase8_real_runner_smoke.sh QQQ 2026-06-18 etf require-option-chain-context
```

### Required Capture

- Full sanitized JSON stdout.
- Stderr byte count.
- Exit code.
- `report_generated` value.
- Evidence labels.
- Report ID or analysis ID only after real readback confirms them.

### Stop Conditions

- Missing prerequisites include anything other than an operator-approved confirmation boundary.
- Output status is `not_ready`, `blocked`, or `failed`.
- The command would need a retry, another symbol, or a changed date.
- The run would require reading or printing secrets.
- The run would add live execution, broker integration, scheduled jobs, automatic retries, or paper-to-live behavior.

### Writeback

Append the result to `docs/operations/phase-13-qqq-gated-preflight.md` under a new provider-backed execution section.

## Report-Review Agent Assignment

### Objective

Review the completed QQQ provider-backed report if, and only if, the Research-Runner Agent records a generated report and confirmed report ID.

### Required Inputs

- Completed QQQ report content.
- Sanitized run metadata.
- Evidence labels.
- Option-chain context included in the mapped report.
- Phase 9 review dimensions:
  - evidence clarity;
  - consistency;
  - risk coverage;
  - options relevance;
  - Chinese readability;
  - research-only safety.

### Required Checks

- Verified market snapshot is present and does not conflict with same-date close claims.
- Options observation includes contract-level context rather than generic placeholder language.
- Trade plan is research-only and includes observation conditions, invalidation conditions, and risk boundaries.
- No broker authority, live order placement, account mutation, scheduled retry, or paper-to-live language appears.

### Stop Conditions

- No completed QQQ report exists.
- Report ID cannot be read back.
- Evidence labels are missing or inconsistent.
- Market data conflicts with verified snapshot data.
- Options context is missing despite the gate being required.

### Writeback

Record review outcome in a new operation doc or in the provider-backed execution section of `docs/operations/phase-13-qqq-gated-preflight.md`.

## Handoff Close Format

```text
Status: succeeded | not_ready | blocked | failed
Scope: QQQ 2026-06-18 etf require-option-chain-context
Evidence: docs/operations/phase-13-qqq-gated-preflight.md
Next decision: <single bounded next action>
Boundary: no extra symbols, retries, broker scope, scheduler, or live execution
```
