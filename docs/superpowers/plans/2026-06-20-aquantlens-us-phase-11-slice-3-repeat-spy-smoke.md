# Phase 11 Slice 3 Repeat-SPY Smoke Plan

**Goal:** Run the approved guarded real-runner wrapper for `SPY` after provider readiness is confirmed.

## Tasks

- [x] Confirm Settings API has a saved write-only `OPENAI_API_KEY`.
- [x] Enable `AQUANTLENS_TRADINGAGENTS_RUNNER_MODE=real-tradingagents`.
- [x] Install TradingAgents real-runner dependencies into the Ubuntu backend venv.
- [x] Run only `scripts/phase8_real_runner_smoke.sh SPY 2026-06-18 etf`.
- [x] Record the sanitized result and residual risks.

## Verification

- Approved wrapper executed.
- Result recorded as `failed`.
- Report generated: `false`.
- Failure was the Yahoo/yfinance SSL market-data runtime path.
- No `.env` file was sourced.
- No secret value was printed, returned, copied, pasted, stored in docs, or committed.

## Non-Goals

- No QQQ run.
- No provider raw response recording.
- No broker integration.
- No live execution.
- No scheduled jobs.
- No automatic retries.
- No paper-to-live workflow.
