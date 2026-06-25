# Phase 13 Report Mapping Improvement

## Scope

This slice fixes the Phase 13 review blocker where the persisted real-runner report mapped the final TradingAgents decision into a thin research-only wrapper and kept options observation at placeholder level.

This is a mapping-layer change only. It does not add broker execution, broker credentials, live trading, scheduled provider-backed jobs, automatic retries, or paper-to-live promotion.

## Implementation

- `backend/app/analysis/tradingagents_runner.py`
  - Added `build_real_runner_trade_plan()`.
  - Added `build_real_runner_options_observation()`.
  - Real-runner `trade_plan` now preserves the original TradingAgents conclusion and expands it into:
    - observation conditions,
    - invalidation conditions,
    - research-only risk boundaries,
    - follow-up review needs.
  - Real-runner `options_observation` now gives a concrete options-risk checklist covering IV, put/call skew, open interest, volume concentration, Gamma exposure, and event volatility risk.
  - Markdown output now includes the mapped options observation and research plan sections.
- `backend/tests/test_tradingagents_runner.py`
  - Added regression coverage for one-word decisions such as `Overweight`.
  - Added assertions that the old placeholder options text is not emitted.
  - Preserved research-only language assertions.

## Verification

Ubuntu isolated copy:

- `/tmp/tradingagents-phase13-mapping`

Commands:

```bash
PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest backend/tests/test_tradingagents_runner.py::test_real_tradingagents_mapping_expands_one_word_decision_and_options_observation -q
PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest backend/tests/test_tradingagents_runner.py -q
PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest backend/tests/test_report_quality.py -q
PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest backend/tests/test_analysis_cli_real_runner_smoke.py -q
```

Results:

- Focused mapping regression: `1 passed`.
- Real-runner mapping tests: `7 passed`.
- Report quality tests: `5 passed`.
- Analysis CLI real-runner smoke-boundary tests: `7 passed`.
- Local `git diff --check -- backend/app/analysis/tradingagents_runner.py backend/tests/test_tradingagents_runner.py` passed.
- Local `py_compile` for the changed runner/test files passed.

## Decision

The mapping blocker is resolved at the unit and quality-contract level.

Do not expand to `QQQ` yet. The next step is to repeat the guarded provider-backed `SPY` persisted analysis and create a fresh review against the improved mapped report.
