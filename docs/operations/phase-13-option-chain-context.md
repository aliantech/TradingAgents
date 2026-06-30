# Phase 13 Option Chain Context

Status: Complete
Last Reviewed: 2026-06-23
Owner: Yasin

## Purpose

Connect persisted option-chain snapshots into the real-runner report mapping so the options observation can include per-contract context when data exists.

This addresses the remaining Phase 13 review blocker that options relevance improved to a risk framework but still lacked contract-level context.

## Implementation

- Added `backend/app/analysis/option_chain_context.py`.
- `start_analysis()` now builds option-chain context from the repository session when persistence is available.
- `TradingAgentsExecutionRequest` now carries `option_chain_context`.
- Real-runner `options_observation` now:
  - includes persisted per-contract option-chain context when available;
  - clearly states when no persisted option-chain snapshot is available;
  - preserves research-only language and does not generate option buy/sell instructions.

The context uses the nearest persisted expiry on or after the analysis date and summarizes:

- covered contract count;
- Call / Put count;
- total volume;
- total open interest;
- top open-interest contracts;
- top Gamma-sensitive contracts.

## Runtime Data Check

Read-only Ubuntu runtime DB check:

```text
SPY []
QQQ [('2026-06-26', 250, 250, 198443, 167045)]
```

Interpretation:

- `QQQ` currently has persisted option-chain snapshots that can feed the new context.
- `SPY` currently has no persisted option-chain snapshots in the runtime DB, so another `SPY` provider-backed run would still state that no per-contract snapshot is available unless SPY option-chain sync runs first.

## Superseded Status

This runtime DB interpretation is historical. A later clean-mirror recheck recorded in `docs/roadmap/phase-13-validation-audit.md` found that `SPY 2026-06-18 etf require-option-chain-context` now returns `not_ready` only because the real-provider confirmation flag is intentionally omitted; it no longer reports missing option-chain context from the current runtime path.

## Verification

Ubuntu isolated copy:

```text
/tmp/tradingagents-phase13-option-context
```

Commands:

```bash
PYTHONPATH=backend /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest backend/tests/test_analysis_option_chain_context.py -q
PYTHONPATH=backend /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest backend/tests/test_analysis_api_persistence.py::test_analysis_api_passes_persisted_option_chain_context_to_runner -q
PYTHONPATH=backend /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest backend/tests/test_analysis_api_persistence.py -q
PYTHONPATH=backend /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest backend/tests/test_analysis_option_chain_context.py backend/tests/test_tradingagents_runner.py backend/tests/test_options_repository.py backend/tests/test_options_api.py -q
PYTHONPATH=backend /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest backend/tests/test_report_quality.py backend/tests/test_analysis_cli_real_runner_smoke.py -q
```

Results:

- Option-chain context helper tests: `2 passed`.
- Focused service integration test: `1 passed`.
- Analysis persistence tests: `8 passed`.
- Runner/options related tests: `17 passed`.
- Report quality and real-runner smoke-boundary tests: `12 passed`.
- Local `git diff --check` passed for changed files.
- Local `py_compile` passed for changed Python files.

## Decision

Per-contract option-chain context is now connected at the code and unit-contract level.

Do not automatically run `QQQ` yet. The next explicit decision is:

- run a guarded `QQQ` provider-backed pilot using the existing QQQ option-chain snapshots; or
- first sync SPY option-chain snapshots, then repeat `SPY` to verify the same symbol with contract-level options context.

This decision is superseded by the later SPY gate recheck. The current bounded operator decision is to run exactly one guarded QQQ pilot or exactly one guarded repeat SPY pilot in an approved environment.

## Boundary

- No OpenAI API call was made for this slice.
- No broker integration was added.
- No live execution was added.
- No live-trading UI control was added.
- No scheduled provider-backed research job was added.
- No automatic retry loop was added.
- No paper-to-live workflow was added.
- No secret values were read, printed, copied, or recorded.
