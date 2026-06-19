# Phase 6 Slice 1 Roadmap and Safety Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish Phase 6 as paper-only workflow hardening with explicit safety boundaries and verifiable follow-on slices.

**Architecture:** This is a documentation-only slice. It adds the Phase 6 roadmap, updates project status, and records the decision in Yasin Brain without touching backend or frontend implementation code.

**Tech Stack:** Markdown documentation, Git, repository safety grep, Yasin Brain project log.

---

### Task 1: Add Phase 6 Roadmap

**Files:**
- Create: `docs/roadmap/phase-6-roadmap.md`

- [ ] **Step 1: Create the roadmap**

Add `docs/roadmap/phase-6-roadmap.md` with these sections:

```markdown
# Phase 6 Roadmap

## Objective

Phase 6 hardens the Phase 5 paper-only MVP into a reviewable, observable, and testable paper workflow.

The goal is not to add live execution. The goal is to make paper trading safer to operate and easier to inspect before any future live-execution discussion.

## Entry State

Phase 5 completed the approved paper-only MVP:

- Paper-only architecture and safety specification.
- Paper trading domain contracts.
- Pure RiskGuard evaluator.
- SQLAlchemy-backed persistence and append-only audit events.
- Human-facing paper intent API with idempotency and review gates.
- Local deterministic paper adapter for simulated fills, cash, and positions.
- Strategy Lab Candidate-to-Paper UI flow.

Reference completion audit: `docs/roadmap/phase-5-completion-audit.md`.

## Design Principles

- Paper-only remains the hard boundary.
- Improve observability before expanding behavior.
- Keep every paper mutation database-backed and audit-backed.
- Prefer small vertical slices that each add user-visible or operator-visible confidence.
- Browser verification should cover critical paper workflows, not decorative UI states.
- No broker SDK, broker credentials, live order methods, trading-scope MCP tools, or paper-to-live controls.

## Phase 6 Slices

### Slice 1: Phase 6 Roadmap and Safety Boundary

Status: planned.

Deliverables:

- Phase 6 roadmap.
- Slice 1 implementation plan.
- Project status update marking Phase 6 as paper workflow hardening.
- Yasin Brain log entry recording that live execution remains out of scope.

Verification:

- Documentation does not authorize live execution.
- Documentation keeps broker credentials, broker account mutation, trading-scope MCP tools, and paper-to-live promotion out of scope.
- Project status points to Phase 6 paper-only hardening.

### Slice 2: Paper Workflow Browser Smoke Test

Status: planned.

Goal:

- Add a minimal browser smoke path for Strategy Lab Candidate-to-Paper UI.

Verification:

- Ubuntu browser or Playwright verification runs successfully.
- Frontend build still passes.
- Safety grep confirms no live-trading UI copy.

### Slice 3: Paper Account and Position Summary API

Status: planned.

Goal:

- Add a compact paper account summary endpoint for UI and operator inspection.

Verification:

- Backend tests prove summary data is account-scoped.
- Backend tests prove no broker account fields or live order fields are exposed.
- Existing paper API tests continue passing.

### Slice 4: Paper PnL Snapshot

Status: planned.

Goal:

- Add paper-only unrealized/realized PnL snapshot logic using explicit caller-provided or stored reference prices.

Verification:

- Pure calculation tests cover supported position states.
- API tests prove PnL output does not include broker account or live execution fields.
- No external market-data fetch is introduced inside paper PnL calculation.

### Slice 5: Paper Risk Dashboard UI

Status: planned.

Goal:

- Add a compact Strategy Lab or paper panel view for paper account exposure and recent paper workflow state.

Verification:

- Frontend build passes.
- Browser smoke covers key visible states.
- UI copy remains paper-only.

### Slice 6: Phase 6 Completion Audit

Status: planned.

Goal:

- Audit Phase 6 after slices are implemented and record residual risks.

Verification:

- Focused backend paper tests pass.
- Full backend regression passes.
- Frontend build passes.
- Browser smoke passes.
- Safety grep only matches negative tests or explicit non-goal docs.
- Project docs and Yasin Brain record completion and remaining live-execution boundary.

## Explicit Non-Goals

- Live broker order placement.
- Broker credential storage or mutation.
- Broker account balance sync.
- Broker order status sync.
- AI-direct live trading authority.
- Trading-scope MCP tools that can reach a broker.
- Live-trading UI controls.
- Automatic promotion from paper to live.
- Production-grade backtesting engine.
- Full OPRA tick/quote archival.
- Multi-user trading operations.

## Completion Criteria

Phase 6 is complete only when:

- Critical paper UI workflow has browser smoke coverage.
- Paper account summary and paper PnL state are inspectable without broker fields.
- Risk and audit visibility are available from the UI or API.
- Focused paper tests, backend regression, frontend build, and browser smoke pass.
- Safety grep confirms no broker SDK, broker credentials, live order methods, trading-scope MCP tools, or paper-to-live controls were introduced.
- Project docs and Yasin Brain record that live execution remains out of scope.
```

- [ ] **Step 2: Verify roadmap safety language**

Run:

```bash
rg -n "live execution|broker credentials|paper-to-live|trading-scope MCP|Status: planned" docs/roadmap/phase-6-roadmap.md
```

Expected: matches only appear in explicit non-goal, safety-boundary, or planned-slice text.

### Task 2: Update Project Status

**Files:**
- Modify: `PROJECT.md`

- [ ] **Step 1: Change status**

Change:

```markdown
Status: Phase 5 Paper-Only MVP Complete
```

To:

```markdown
Status: Phase 6 Paper Workflow Hardening
```

- [ ] **Step 2: Add Phase 6 snapshot text**

In `Current Progress Snapshot`, add a new bullet after the Phase 5 bullet:

```markdown
- Current Phase 6 state: Phase 6 is planned as paper-only workflow hardening. The next slices focus on browser smoke verification, paper account and position summary, paper PnL snapshots, and paper risk dashboard visibility. Live broker execution, broker credentials, broker account mutation, AI-directed live trading, trading-scope MCP tools, live-trading UI controls, and automatic paper-to-live promotion remain out of scope.
```

- [ ] **Step 3: Add key documents**

Add these entries to `Key Documents`:

```markdown
- `docs/roadmap/phase-6-roadmap.md`
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-6-slice-1-roadmap.md`
```

- [ ] **Step 4: Verify project status**

Run:

```bash
rg -n "Phase 6|phase-6|paper-to-live|live broker execution" PROJECT.md
```

Expected: Phase 6 status and document links are present; live execution appears only as out-of-scope language.

### Task 3: Record Yasin Brain Log

**Files:**
- Modify: `/Users/yasin/Documents/Yasin AI OS/04-Projects/aquantlens/LOG.md`

- [ ] **Step 1: Append project log entry**

Append:

```markdown
## 2026-06-20 — TradingAgents US/options Phase 6 Paper Workflow Hardening plan

- Started Phase 6 for the separate TradingAgents-based AQuantLens US/options branch.
- Added docs/roadmap/phase-6-roadmap.md and docs/superpowers/plans/2026-06-20-aquantlens-us-phase-6-slice-1-roadmap.md.
- Phase 6 is paper-only workflow hardening: browser smoke verification, paper account and position summary, paper PnL snapshots, and paper risk dashboard visibility.
- Live broker execution, broker credentials, broker account mutation, AI-directed live trading, trading-scope MCP tools, live-trading UI controls, and automatic paper-to-live promotion remain out of scope.
- No backend implementation code, frontend implementation code, broker integration, network execution, credential handling, or live execution was added in this planning step.
- No secrets were read, printed, copied, or recorded.
```

- [ ] **Step 2: Verify recent log**

Run:

```bash
tail -40 "/Users/yasin/Documents/Yasin AI OS/04-Projects/aquantlens/LOG.md"
```

Expected: the Phase 6 log entry is present and does not include secrets.

### Task 4: Final Documentation Verification and Commit

**Files:**
- Verify: `docs/roadmap/phase-6-roadmap.md`
- Verify: `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-6-slice-1-roadmap.md`
- Verify: `PROJECT.md`

- [ ] **Step 1: Check repository status**

Run:

```bash
git status --short --branch
```

Expected: only the Phase 6 documentation files and `PROJECT.md` are changed.

- [ ] **Step 2: Safety grep**

Run:

```bash
rg -n "broker SDK|broker credentials|live order|live execution|paper-to-live|trading-scope MCP|credential" PROJECT.md docs/roadmap/phase-6-roadmap.md docs/superpowers/plans/2026-06-20-aquantlens-us-phase-6-slice-1-roadmap.md
```

Expected: matches only appear in non-goals, safety checks, and out-of-scope statements.

- [ ] **Step 3: Commit**

Run:

```bash
git add PROJECT.md docs/roadmap/phase-6-roadmap.md docs/superpowers/plans/2026-06-20-aquantlens-us-phase-6-slice-1-roadmap.md
git commit -m "docs: plan phase 6 paper hardening"
```

Expected: commit succeeds with only documentation changes.

- [ ] **Step 4: Push**

Run:

```bash
git push origin aquantlens-us
```

Expected: push succeeds.

## Self-Review

- Spec coverage: the plan covers roadmap creation, project status update, Yasin Brain logging, safety verification, commit, and push.
- Placeholder scan: no placeholder wording or unspecified test steps remain.
- Type consistency: this is a documentation-only plan and does not introduce code types or method names.
