# Phase 13 Approved Pilot Runbook

Status: Operator handoff, provider run not executed by Codex
Last Reviewed: 2026-07-01
Owner: Yasin

## Purpose

Define the exact one-run operator path for the pending Phase 13 guarded provider-backed pilot.

This runbook is for an approved environment only. It does not authorize Codex to send runtime context or research input to an external LLM/provider from a restricted execution environment.

## Assumptions

- The operator has explicitly approved one real provider-backed research smoke.
- The clean checkout is `/home/yasin/workspace/TradingAgents`.
- The runtime database remains the approved TradingAgents runtime database for this branch.
- Provider secrets are already configured in the approved runtime and are not printed, copied, or recorded.
- Exactly one symbol is selected before execution.

## One-Run Choice

Choose one, and only one, before executing:

- Preferred continuation: `QQQ 2026-06-18 etf require-option-chain-context`.
- Repeat-control alternative: `SPY 2026-06-18 etf require-option-chain-context`.

Do not run both from the same decision. Do not change the date or add another symbol from the same result.

## Command

Run from the clean mirror:

```bash
cd /home/yasin/workspace/TradingAgents
```

For the preferred `QQQ` pilot:

```bash
AQUANTLENS_DATABASE_URL=sqlite:////home/yasin/workspace/TradingAgents/backend/aquantlens_us.db \
AQUANTLENS_TRADINGAGENTS_RUNNER_MODE=real-tradingagents \
PATH=/home/yasin/workspace/TradingAgents/backend/.venv/bin:$PATH \
scripts/phase8_real_runner_smoke.sh QQQ 2026-06-18 etf require-option-chain-context
```

For the repeat-control `SPY` pilot:

```bash
AQUANTLENS_DATABASE_URL=sqlite:////home/yasin/workspace/TradingAgents/backend/aquantlens_us.db \
AQUANTLENS_TRADINGAGENTS_RUNNER_MODE=real-tradingagents \
PATH=/home/yasin/workspace/TradingAgents/backend/.venv/bin:$PATH \
scripts/phase8_real_runner_smoke.sh SPY 2026-06-18 etf require-option-chain-context
```

## Required Capture

Record only sanitized operational evidence:

- selected symbol;
- command exit code;
- full JSON stdout;
- stderr byte count and sanitized stderr summary, if any;
- `status`;
- `missing`;
- `report_generated`;
- `evidence_labels`;
- report ID or analysis ID only after readback confirms it.

Do not record secret values, token names, provider request bodies, raw prompts, or private credential paths.

## Stop Rules

Stop immediately if any of these occur:

- `status` is `not_ready`, `blocked`, or `failed`;
- `missing` contains anything other than an understood operator boundary before execution;
- option-chain context is reported missing;
- provider/model/runtime errors appear;
- report ID cannot be read back;
- output requires a retry, a second symbol, or a changed date;
- any step would require reading or printing secrets.

## Review Gate

Only if `status` is `succeeded`, `report_generated` is `true`, and a report ID is confirmed by readback:

1. Review the report using the Phase 9 dimensions:
   - evidence clarity;
   - consistency;
   - risk coverage;
   - options relevance;
   - Chinese readability;
   - research-only safety.
2. Confirm the report contains the verified market snapshot evidence label.
3. Confirm options observation includes contract-level option-chain context.
4. Confirm the trade plan remains research-only and includes observation conditions, invalidation conditions, and risk boundaries.
5. Record the review outcome before deciding any next symbol or repeat run.

## Writeback

Write the result to the matching operation evidence:

- `QQQ`: append to `docs/operations/phase-13-qqq-gated-preflight.md`.
- `SPY`: append to `docs/roadmap/phase-13-validation-audit.md` or create a dedicated repeat-SPY operation record if a report is generated.

Then update:

- `docs/roadmap/phase-13-roadmap.md`;
- `docs/operations/phase-13-codex-agent-handoff.md`;
- Yasin Brain `04-Projects/aquantlens/LOG.md`, if the run changes project state.

## Boundary

- No broker integration.
- No live execution.
- No live-trading UI control.
- No scheduled provider-backed job.
- No automatic retry loop.
- No paper-to-live workflow.
- No bulk symbol expansion.
