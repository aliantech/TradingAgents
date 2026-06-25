# Phase 13 Option Chain Readiness Gate

Status: Complete
Last Reviewed: 2026-06-23
Owner: Yasin

## Purpose

Add an explicit option-chain readiness gate for guarded real-runner smoke runs.

This closes the framework gap where a provider-backed pilot could be launched for a symbol without persisted per-contract option-chain context, leaving the report to discover the missing data after the provider call.

## Implementation

- `app.analysis.cli real-runner-smoke` now accepts:

```text
--require-option-chain-context
```

- `scripts/phase8_real_runner_smoke.sh` now accepts an optional fourth argument:

```text
require-option-chain-context
```

- When the gate is enabled:
  - the CLI builds option-chain context from the runtime database before invoking the runner;
  - if no persisted option-chain context exists, the smoke returns `not_ready`;
  - the real runner is not called;
  - no report is generated.

The default smoke behavior is unchanged. Operators must explicitly opt into the option-chain readiness gate.

## Runtime Gate Check

Isolated Ubuntu copy:

```text
/tmp/tradingagents-phase13-readiness-gate
```

Runtime DB context check from the isolated backend directory:

```text
SPY_CONTEXT False
QQQ_CONTEXT True
```

SPY gated smoke command:

```bash
PATH=/home/yasin/workspace/TradingAgents/backend/.venv/bin:$PATH \
  scripts/phase8_real_runner_smoke.sh SPY 2026-06-18 etf require-option-chain-context
```

Result:

```text
EXIT:1
STDOUT_BYTES:312
STDERR_BYTES:0
```

Smoke JSON:

```json
{"symbol": "SPY", "status": "not_ready", "runner_mode": "real-tradingagents", "llm_provider": "openai", "model": "gpt-5.5", "missing": ["persisted option-chain context"], "progress": [], "report_generated": false, "evidence_labels": [], "error_message": "Manual real-runner smoke prerequisites are incomplete."}
```

Interpretation:

- `SPY` was blocked before real-runner/provider execution because no persisted SPY option-chain context exists.
- `QQQ` has option-chain context available in the runtime DB, but no QQQ provider-backed run was started in this slice.

## Verification

Commands:

```bash
PYTHONPATH=backend /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest backend/tests/test_analysis_cli_real_runner_smoke.py backend/tests/test_phase8_real_runner_smoke_script.py backend/tests/test_analysis_option_chain_context.py backend/tests/test_analysis_api_persistence.py -q
PYTHONPATH=backend /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest backend/tests/test_tradingagents_runner.py backend/tests/test_report_quality.py -q
```

Results:

- CLI/script/context/persistence tests: `21 passed`.
- Runner/report-quality tests: `12 passed`.
- Local `git diff --check` passed for the changed files.
- Local `py_compile` passed for changed CLI/test files.

## Decision

The option-chain readiness gate is now available for guarded provider-backed pilots.

Next decision:

- use `require-option-chain-context` for a guarded QQQ pilot, because QQQ currently has persisted option-chain context; or
- sync SPY option-chain snapshots first, then repeat SPY with the gate enabled.

## Boundary

- No OpenAI API call was made for this slice.
- No provider-backed research run was started.
- No broker integration was added.
- No live execution was added.
- No live-trading UI control was added.
- No scheduled provider-backed research job was added.
- No automatic retry loop was added.
- No paper-to-live workflow was added.
- No secret values were read, printed, copied, or recorded.
