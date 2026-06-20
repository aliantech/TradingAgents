# Phase 8 Slice 1 Roadmap and Operations Boundary Plan

> **For agentic workers:** This slice is planning and boundary definition only. Do not add runtime code.

**Goal:** Define Phase 8 as research operations hardening for the Phase 7 execution path while preserving the no-live-trading safety boundary.

**Architecture:** Document the staged path from runtime-gated research execution to settings visibility, guarded manual smoke, report-quality validation, diagnostics, and completion audit.

---

## File Structure

- Create: `docs/roadmap/phase-8-roadmap.md`
  - Define objective, entry state, slices, non-goals, and completion criteria.
- Create: `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-8-slice-1-roadmap.md`
  - Record Slice 1 plan and verification.
- Modify: `PROJECT.md`
  - Mark current status as Phase 8 research operations hardening.
  - Add Phase 8 roadmap to key documents.
- Modify: `/Users/yasin/Documents/Yasin AI OS/04-Projects/aquantlens/LOG.md`
  - Record that Phase 8 is planned for the separate TradingAgents US/options branch.

## Assumptions

- The next highest-value step after Phase 7 is making the research execution path operable and diagnosable.
- Deterministic mode should remain the default until real provider-backed runs are intentionally configured.
- Manual real-runner smoke should be guarded before any scheduling or background execution is considered.

## Safety Boundary

This phase must not add:

- Broker SDKs.
- Broker credentials.
- Broker account mutation.
- Live order methods.
- AI-directed live trading.
- Trading-scope MCP tools.
- Live-trading UI controls.
- Paper-to-live promotion.
- Automated provider calls in tests.

## Tasks

- [x] Create Phase 8 roadmap.
- [x] Define planned slices for runner settings UX, guarded manual real-runner smoke, report-quality validation, diagnostics, and completion audit.
- [x] Keep live execution and broker scope out of Phase 8.
- [x] Update project status.
- [x] Update Yasin Brain log.

## Verification

- Documentation points Phase 8 to research operations hardening.
- Documentation keeps live execution out of scope.
- No runtime code was added.

