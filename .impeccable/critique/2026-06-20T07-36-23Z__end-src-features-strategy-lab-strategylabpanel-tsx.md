---
target: frontend/src/features/strategy-lab/StrategyLabPanel.tsx
total_score: 38
p0_count: 0
p1_count: 0
timestamp: 2026-06-20T07-36-23Z
slug: end-src-features-strategy-lab-strategylabpanel-tsx
---
# Critique: frontend/src/features/strategy-lab/StrategyLabPanel.tsx

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 4 | Workflow steps now distinguish complete/current/empty/updating instead of implying all states are complete. |
| 2 | Match System / Real World | 4 | Research-only, candidate review, RiskGuard, human approval, and paper simulation remain explicit and credible. |
| 3 | User Control and Freedom | 4 | Retry, cancel, archive, compare, review, reject, and paper actions are available with visible recovery paths. |
| 4 | Consistency and Standards | 4 | Candidate Board, Experiment Rail, and Saved Table now share grouped action language. |
| 5 | Error Prevention | 4 | Paper Submit remains gated by RiskGuard and human approval, with clear blockers. |
| 6 | Recognition Rather Than Recall | 4 | Compare / Manage / Review labels reduce the burden of A/B and icon-only controls. |
| 7 | Flexibility and Efficiency | 4 | The dense layout remains efficient for repeat expert workflows while preserving scan labels. |
| 8 | Aesthetic and Minimalist Design | 3 | The page is still a broad workbench with many panels, but the density fits the domain. |
| 9 | Error Recovery | 4 | Retry actions are colocated and paper retries now follow the failed action. |
| 10 | Help and Documentation | 3 | Paper-only boundaries are strong; broader first-time education remains intentionally light. |
| **Total** | | **38/40** | **Excellent: ready for engineering verification and commit hygiene.** |

## Anti-Patterns Verdict

This does not read as AI-generated. It avoids gradient text, glassmorphism, broad ghost-card shadows, finance-theater styling, over-rounded cards, decorative motion, and marketing SaaS composition. The interface reads as an internal expert workbench.

The deterministic detector returned `[]` for `frontend/src/features/strategy-lab/StrategyLabPanel.tsx`.

Browser overlay evidence was not available in this run. The fallback signal is source-level review, clean CLI detector output, local TypeScript verification, and prior Ubuntu build/Playwright smoke success.

## Overall Impression

The Strategy Lab surface has moved from "credible but dense" to "institution-grade and operationally clear." The primary path is now visible, paper-only boundaries are repeated where risk decisions happen, action clusters are grouped consistently, and error states offer recovery instead of becoming dead ends.

The remaining tradeoff is deliberate: this is still a dense desktop-first expert workbench. That is acceptable for the product register and current phase.

## What's Working

1. The workflow strip now carries real state semantics instead of decorative completion.
2. Candidate, rail, and saved-table actions use a shared Compare / Manage / Review vocabulary.
3. Paper Review is clear, sober, and paper-only at every high-stakes step.
4. Retry behavior is materially safer after paper operation failures.

## Priority Issues

### [P3] Desktop-first table density remains intentional

Why it matters: Candidate and saved experiment tables are still horizontal-scroll experiences on narrow screens. For a desktop research workbench this is acceptable, but it should be treated as an explicit product choice.

Fix: No immediate change required. If mobile operation becomes a real target, convert the tables into stacked row cards below tablet width.

Suggested command: `$impeccable adapt frontend/src/features/strategy-lab/StrategyLabPanel.tsx`

### [P3] Loading skeletons are lightweight, not data-shaped

Why it matters: The new skeleton rows are calmer than text-only loading states, but they do not mirror exact table structure. This is fine for current quality bar.

Fix: Only upgrade to table-shaped skeletons if this becomes a flagship surface.

Suggested command: `$impeccable polish frontend/src/features/strategy-lab/StrategyLabPanel.tsx`

## Persona Red Flags

**Power Research Operator**: No blocking red flags remain. The surface is dense but now better labeled.

**Risk Reviewer**: Paper Review has clear scope, current status, RiskGuard output, human gate, blockers, and audit events.

**First-Time Internal User**: The user can now infer the main path from the workflow strip and grouped actions. Some product knowledge is still assumed, which is acceptable for an internal expert tool.

## Minor Observations

- `Saved Experiment Table` could eventually be renamed `Saved Experiment Archive`, but this is not blocking.
- No color, typography, or motion work is needed now.
- The next meaningful step is build/test/commit hygiene, not more design iteration.

## Questions to Consider

- Should the accepted desktop-first table behavior be documented in Phase 6 notes?
- Should this UI/design work be committed separately from broader Phase 6 backend/docs changes?
