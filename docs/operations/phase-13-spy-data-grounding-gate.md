# Phase 13 SPY Data-Grounding Gate

Status: Complete
Last Reviewed: 2026-06-21
Owner: Yasin

## Purpose

Record the first Phase 13 fix after the Phase 12 provider-backed `SPY` report review failed data-grounding.

## Problem

The first persisted provider-backed `SPY` report was not approved for expansion because it stated `SPY` close `746.74` for `2026-06-18`, while the Phase 12 direct Yahoo chart validation returned `549.33` for the same date.

This showed that prompt-level instructions and the market analyst's verified snapshot tool were not enough. The persistence path still trusted LLM market text unless the later human review caught the discrepancy.

## Change

- Real-runner report mapping now computes a deterministic verified market-data snapshot for the requested symbol and analysis date.
- The snapshot is inserted into `market_background`, `technical_analysis`, and report markdown.
- Real-runner reports now include evidence label `direct-yahoo-chart-verified-snapshot`.
- Report quality validation now rejects real-runner reports when same-date `Close` / `收盘` claims conflict with the verified snapshot close.

## Verification

Ran in isolated Ubuntu copy synced from the Mac checkout:

```bash
cd /tmp/tradingagents-mac-phase12-grounding-verify/backend
PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest \
  tests/test_report_quality.py::test_quality_contract_rejects_real_runner_close_conflict_with_verified_snapshot \
  tests/test_tradingagents_runner.py -q
```

Result:

```text
7 passed
```

Additional focused regression:

```bash
cd /tmp/tradingagents-mac-phase12-grounding-verify/backend
PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest \
  tests/test_report_quality.py \
  tests/test_tradingagents_runner.py \
  tests/test_analysis_api_persistence.py::test_analysis_api_rejects_invalid_report_quality_before_persistence -q
```

Result:

```text
12 passed
```

Manual real-runner smoke CLI mocked gate regression:

```bash
cd /tmp/tradingagents-mac-phase12-grounding-verify/backend
PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest \
  tests/test_analysis_cli_real_runner_smoke.py -q
```

Result:

```text
7 passed
```

## Decision

Do not expand to `QQQ` yet.

Next action is to repeat the guarded `SPY` provider-backed review path. A conflicting SPY report should now fail report quality before persistence instead of being saved as a completed report.

## Boundary

- No broker integration was added.
- No live execution was added.
- No live-trading UI control was added.
- No scheduled provider-backed research job was added.
- No automatic retry loop was added.
- No paper-to-live workflow was added.
- No secret values were read, printed, copied, or recorded.
