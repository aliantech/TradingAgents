# Phase 10 Slice 3 Guarded Real-Runner Smoke Plan

**Goal:** Execute the approved guarded real-runner smoke wrapper for the SPY first case and record sanitized non-secret metadata.

## Tasks

- [x] Use an isolated Ubuntu temp copy instead of the dirty Ubuntu main workspace.
- [x] Enable the explicit real-runner runtime gate in a temporary SQLite database.
- [x] Run only `scripts/phase8_real_runner_smoke.sh SPY 2026-06-18 etf`.
- [x] Record the sanitized result and residual risks.

## Verification

- Wrapper result recorded as `not_ready`.
- Missing readiness gate recorded as `OPENAI_API_KEY`.
- No `.env` file was sourced.
- No secret value was read, printed, copied, pasted, stored, or committed.
- No real LLM provider call was made because readiness failed before runner invocation.

## Non-Goals

- No direct CLI bypass around the wrapper.
- No runtime code changes.
- No broker integration.
- No live execution.
- No scheduled jobs.
- No automatic retries.
- No paper-to-live workflow.
