---
target: frontend/src/features/strategy-lab/StrategyLabPanel.tsx
total_score: 35
p0_count: 0
p1_count: 0
timestamp: 2026-06-20T07-24-42Z
slug: end-src-features-strategy-lab-strategylabpanel-tsx
---
# Critique: frontend/src/features/strategy-lab/StrategyLabPanel.tsx

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | The top path is clearer now, but every workflow chip uses a green check icon even for incomplete states such as "No draft" or "No candidates." |
| 2 | Match System / Real World | 4 | Research-only, candidate review, RiskGuard, human review, and local paper simulation map well to the real workflow. |
| 3 | User Control and Freedom | 4 | Open, compare, archive, reject, cancel, and retry paths are visible and recoverable. |
| 4 | Consistency and Standards | 4 | Candidate/Saved table actions now use visible groups, shared primitives, and clearer labels. |
| 5 | Error Prevention | 4 | Paper Submit remains gated by RiskGuard and human approval, with visible blockers. |
| 6 | Recognition Rather Than Recall | 4 | Compare/Review/Manage group labels reduce the meaning burden around A/B and icon buttons. |
| 7 | Flexibility and Efficiency | 3 | The dense layout works for expert users; Experiment Rail still carries many compact actions. |
| 8 | Aesthetic and Minimalist Design | 3 | The surface is more organized, but the page still presents rail, board, paper review, audit table, and saved table in one long workbench. |
| 9 | Error Recovery | 3 | Retry actions are now colocated with most failures; paper-error retry can still be more state-specific than "Run RiskGuard." |
| 10 | Help and Documentation | 3 | Paper-only copy is strong; the broader Strategy Lab workflow is clearer but still assumes some local product knowledge. |
| **Total** | | **35/40** | **Strong: institution-grade and much clearer; remaining work is semantic status polish and final verification.** |

## Anti-Patterns Verdict

This still does not look AI-generated. The interface avoids the saturated slop tells: no gradient text, no decorative glass, no broad ghost-card shadows, no hero-metric template, no arbitrary decorative finance palette, and no over-rounded cards. It reads as a real expert workbench.

The deterministic detector returned `[]` for `frontend/src/features/strategy-lab/StrategyLabPanel.tsx`. No automated slop or local quality findings were reported.

Browser overlay evidence was not available in this run. The fallback signal is source-level review plus the clean CLI detector result.

## Overall Impression

The previous critique's biggest issues have largely been addressed. The screen now has a clearer operating story: Catalog -> Preview -> Candidate -> Paper. Candidate Board is more visibly the candidate/paper action surface. Saved Experiment Table has been demoted to compare/archive. Error states now include recovery actions. That is a real improvement.

The remaining design debt is no longer structural; it is semantic polish. The status chips need to distinguish complete/current/blocked states better, and the Experiment Rail should either remain an expert quick-action rail intentionally or lose some repeated review controls.

## What's Working

1. The primary workflow is now visible at the top instead of being inferred from scattered panels.
2. Candidate Board action groups make A/B and paper draft actions much easier to scan.
3. RetryAlert improves error recovery without adding modal friction or a new component language.
4. Paper Review remains the strongest high-stakes section: scope, local-only boundary, RiskGuard, human gate, blockers, and submit state all read clearly.

## Priority Issues

### [P2] Workflow chips overstate incomplete states

Why it matters: Catalog, Preview, Candidate, and Paper all show the same green check icon, even when the value is "No candidates" or "No draft." That creates a subtle semantic mismatch: incomplete states visually look complete.

Fix: Give workflow steps a tone/status model: complete, current, blocked/empty, updating. Use CheckCircle only for complete states; use neutral or pending icons for empty/current states.

Suggested command: `$impeccable polish frontend/src/features/strategy-lab/StrategyLabPanel.tsx`

### [P2] Paper error retry can be more state-specific

Why it matters: `RetryAlert` is much better, but when a paper operation fails the fallback action is "Run RiskGuard" whenever a paper intent exists. After a failed approve, submit, or cancel, that retry label may not match the failed action.

Fix: Track the last attempted paper action or derive a safer retry label from current status: RiskGuard for draft/awaiting review, Approve Paper after pass, Paper Submit after approved, Reload accounts when no intent exists.

Suggested command: `$impeccable harden frontend/src/features/strategy-lab/StrategyLabPanel.tsx`

### [P3] Experiment Rail still duplicates review actions

Why it matters: Saved Experiment Table was successfully demoted, but Experiment Rail still exposes open, duplicate, compare A/B, archive, reviewed, candidate, and reject in a compact button cluster. For power users this is efficient; for first-time users it is still dense.

Fix: Either leave it as an intentional expert quick-action rail, or mirror the new grouping language there as well: Compare / Manage / Review.

Suggested command: `$impeccable layout frontend/src/features/strategy-lab/StrategyLabPanel.tsx`

### [P3] Loading states remain text-only

Why it matters: "Loading experiments" and "Loading candidates" are clear, but visually weaker than the rest of the workbench. This is acceptable for now, but skeleton rows would make refreshes feel more stable.

Fix: Add compact skeleton/table placeholder rows only if this screen is being polished for a flagship release.

Suggested command: `$impeccable polish frontend/src/features/strategy-lab/StrategyLabPanel.tsx`

## Persona Red Flags

**Power Research Operator**: The main path is much faster to scan now. The remaining red flag is Experiment Rail: it still has many compact actions in one row, which is powerful but visually busy.

**Risk Reviewer**: Paper Review is in good shape. The remaining risk-review concern is that the top workflow chip can display "Paper: No draft" with a green check icon, which may visually imply all is well.

**First-Time Internal User**: Candidate Board labels now help. The remaining stumbling point is understanding whether Experiment Rail is a quick action rail or another authoritative review surface.

## Minor Observations

- `Saved Experiment Table` may be better named `Experiment Archive` or `Saved Experiment Archive` now that it is compare/archive oriented.
- The clean detector result is meaningful here because the remaining issues are semantic design judgments, not slop-pattern defects.
- The Paper Review copy remains appropriately sober and paper-only.
- No further color or typography work is needed right now.

## Questions to Consider

- Should Experiment Rail stay as a power-user quick action surface, or should it be simplified to read-only navigation plus compare?
- Is the workflow strip meant to show completion state, current state, or availability? It should choose one model.
- Should this screen now move from design iteration to Ubuntu build/Playwright verification?
