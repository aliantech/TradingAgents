# Codex Agent Roles

Status: Active
Last Reviewed: 2026-07-01
Owner: Yasin

## Purpose

Define lightweight Codex execution roles for the AQuantLens US/options branch. These roles guide how a Codex session should run bounded research operations and report review work. They are not backend services, MCP tools, autonomous schedulers, or trading agents.

## Shared Rules

All Codex agent roles must follow the project execution boundary:

- Read `AGENTS.md`, `PROJECT.md`, and the relevant roadmap/operations docs before acting.
- Use Mac local work for reading, editing, documentation, and lightweight static checks.
- Use Ubuntu or an isolated Ubuntu temp clone for runtime verification when execution is needed.
- Do not read or print secrets, `.env` values, credential stores, browser sessions, private keys, or token caches.
- Do not bypass readiness gates, report-quality gates, or research-only safety wording.
- Do not add broker integration, live execution, live-trading UI controls, automatic retries, scheduled provider-backed jobs, or paper-to-live promotion.
- Stop and record `not_ready`, `blocked`, or `failed` when a gate or execution policy blocks progress.

## Research-Runner Agent

### Responsibility

Prepare and run bounded research-runner validation steps for the approved symbol/date/scope.

### Inputs

- Symbol, analysis date, and asset type.
- Runner mode and provider-readiness requirements.
- Required gates, such as `require-option-chain-context`.
- Relevant operation doc, for example `docs/operations/phase-13-qqq-gated-preflight.md`.

### Allowed Work

- Check branch, worktree, latest commit, and runtime-readiness docs.
- Run no-provider preflight checks that do not call an external LLM/provider.
- In an approved environment, run the documented guarded smoke command exactly once for the approved symbol/date/scope.
- Capture sanitized JSON status, stderr byte count, whether a report was generated, and evidence labels.
- Update operation docs with factual results.

### Stop Conditions

- Workspace has unrelated dirty changes that would be overwritten by sync.
- Readiness output includes missing prerequisites.
- Execution policy blocks external provider/LLM calls.
- Runtime output is `not_ready`, `blocked`, or `failed`.
- The requested run would expand to another symbol, retry automatically, or alter trading scope.

### Verification

- Confirm the command either stopped before provider execution with a clear `missing` list or produced a single bounded smoke result.
- Confirm no secret values appear in logs or docs.
- Confirm generated documentation records report IDs only after real readback.

## Report-Review Agent

### Responsibility

Review completed research reports for quality, evidence, safety, and expansion readiness.

### Inputs

- Report ID or operation doc containing a completed report result.
- Relevant report-quality contract and review dimensions.
- The exact phase decision being considered, such as SPY repeat, QQQ expansion, or stop/fix-first.

### Allowed Work

- Read completed report content and sanitized run metadata.
- Score evidence clarity, consistency, risk coverage, options relevance, Chinese readability, and research-only safety using the existing review contract.
- Identify data-grounding conflicts, missing option-chain context, placeholder options language, one-word trade plans, and unsafe trading-authority wording.
- Record review outcome and next decision in the relevant operation doc.

### Stop Conditions

- No completed report exists.
- Report data conflicts with verified market snapshots.
- Options relevance is not contract-level when contract-level validation is required.
- Research-only safety wording is missing or weakened.
- The next action would require a new provider-backed run without explicit operator approval.

### Verification

- Confirm the review references concrete evidence from the report or operation record.
- Confirm expansion decisions are explicit: `approved`, `fix_first`, `blocked`, or `not_ready`.
- Confirm the review does not invent market data, option-chain evidence, or runtime state.

## Handoff Format

Each role should close with:

```text
Status: succeeded | not_ready | blocked | failed
Scope: <symbol/date/phase or report id>
Evidence: <doc path or sanitized command result>
Next decision: <single bounded next action>
Boundary: <what was not run or not changed>
```

## Current Phase 13 Assignment

- Research-Runner Agent: `QQQ 2026-06-18 etf require-option-chain-context` is readiness-gate ready, but real provider-backed execution is blocked in the current execution environment. Evidence: `docs/operations/phase-13-qqq-gated-preflight.md`.
- Report-Review Agent: wait for a completed `QQQ` provider-backed report from an approved environment before reviewing expansion readiness.
