---
target: frontend/src/features/strategy-lab/StrategyLabPanel.tsx
total_score: 31
p0_count: 0
p1_count: 1
timestamp: 2026-06-20T07-16-16Z
slug: end-src-features-strategy-lab-strategylabpanel-tsx
---
# Critique: frontend/src/features/strategy-lab/StrategyLabPanel.tsx

## Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Workflow chips, loading labels, and Paper Review next-step state are strong, but some async table refreshes still read as plain text rather than structured loading/retry states. |
| 2 | Match System / Real World | 4 | The language now clearly separates research-only preview, human review, RiskGuard, and local paper simulation. |
| 3 | User Control and Freedom | 3 | Cancel/archive/reject/open paths exist, but duplicate action surfaces make it harder to know which control path is primary. |
| 4 | Consistency and Standards | 3 | Shared shadcn primitives are consistent; A/B comparison buttons and dense icon rows still need clearer conventions. |
| 5 | Error Prevention | 4 | Paper Submit is gated by RiskGuard and human approval; locked controls now explain blockers. |
| 6 | Recognition Rather Than Recall | 3 | Paper Review is self-explanatory, but experiment/candidate action icons still require remembering what A/B, badge-check, and archive mean. |
| 7 | Flexibility and Efficiency | 3 | Dense rail, tables, filters, and compare controls serve power users, but keyboard/command efficiency is not visible. |
| 8 | Aesthetic and Minimalist Design | 3 | Institution-grade density fits the brief, though the page still exposes many equal-weight panels at once. |
| 9 | Error Recovery | 2 | Errors are shown, but most recovery is implicit; retry actions are not consistently colocated with failures. |
| 10 | Help and Documentation | 3 | Inline paper-only copy is good; broader Strategy Lab workflow still relies on the operator already knowing the sequence. |
| **Total** | | **31/40** | **Good: credible expert workbench; remaining work is hierarchy and recovery polish.** |

## Anti-Patterns Verdict

This does not look AI-generated. It avoids the common tells: no gradient text, no decorative glass, no hero metric template, no ornamental card grid, no excessive rounded cards, and no finance-theater palette. The interface reads as a real internal workbench.

The deterministic detector returned `[]` for `frontend/src/features/strategy-lab/StrategyLabPanel.tsx`. It did not find slop-family issues or local quality hits.

Browser overlay evidence was not available in this run. The fallback signal is source-level review plus the clean CLI detector result.

## Overall Impression

Strategy Lab now has the right institutional posture. The Paper Review section is the strongest part: it makes scope, status, risk gate, human gate, next step, and locked controls explicit without implying live execution.

The largest remaining opportunity is hierarchy. The page offers research controls, preview, backtest, rail, comparison, candidate board, paper review, audit events, and saved table in one continuous surface. That is useful for an expert, but too many action clusters compete at the same visual priority.

## What's Working

1. Paper-only safety is now explicit at the decision point, not buried in general copy.
2. RiskGuard and human review are separated from paper simulation, which matches the product boundary.
3. The visual vocabulary is restrained and consistent: small radius, neutral surfaces, tokenized buttons, real tables, and low-drama status color.

## Priority Issues

### [P1] The workflow still exposes too many equal-weight decision zones

Why it matters: A research operator can do many things from this screen: tune parameters, save, compare, mark reviewed/candidate/rejected, create paper drafts, run RiskGuard, approve, submit, archive, duplicate, and refresh. The surface is powerful, but the primary path is still not visually dominant enough.

Fix: Give the screen a clearer progression: Preview -> Candidate -> Paper Review. Keep secondary saved-table actions available, but lower their visual priority or place them behind row-level affordances that do not compete with Paper Review.

Suggested command: `$impeccable distill frontend/src/features/strategy-lab/StrategyLabPanel.tsx`

### [P2] Duplicate experiment action models increase recall burden

Why it matters: The Experiment Rail, Candidate Board, and Saved Experiment Table all expose overlapping actions: A/B compare, open, archive, reject, candidate/reviewed. This is efficient once learned, but confusing during active review because the operator must remember which surface is authoritative.

Fix: Establish one primary action surface for candidate review and one secondary archive/history surface. Keep A/B comparison labels, but add compact visible group labels or consolidate repeated row controls.

Suggested command: `$impeccable layout frontend/src/features/strategy-lab/StrategyLabPanel.tsx`

### [P2] Error recovery is visible but not actionable enough

Why it matters: Errors currently appear as alerts, but most do not include a colocated retry or next recovery action. In an operational research workbench, failed catalog/candidate/experiment/paper calls should immediately offer the next safe action.

Fix: Add contextual retry actions to key error states: reload catalog, reload experiments, reload candidates, retry RiskGuard, retry paper submit where safe.

Suggested command: `$impeccable harden frontend/src/features/strategy-lab/StrategyLabPanel.tsx`

### [P2] Compact icon and A/B controls still depend on learned meaning

Why it matters: The icon buttons have ARIA labels, but visible meaning is still sparse. Sighted users scanning the table see A, B, archive, badge-check, and reject without a clear action legend. This is acceptable for expert repeat use, but it slows first-time operation.

Fix: Add one compact visible action grouping or legend in the candidate/saved table headers, or convert the least obvious icon-only controls to short text on wider rows.

Suggested command: `$impeccable clarify frontend/src/features/strategy-lab/StrategyLabPanel.tsx`

### [P3] Mobile adaptation protects Paper Review, but tables remain desktop-first

Why it matters: Horizontal scroll is acceptable for dense financial tables, but on narrow screens the candidate and saved tables still behave as desktop artifacts. That is probably fine for this desktop-first product, but it means mobile use is review-only rather than comfortable operation.

Fix: If narrow-screen operation matters, create stacked row cards for Candidate Board and Saved Experiment Table below the tablet breakpoint. If desktop is the true target, document this as an accepted constraint.

Suggested command: `$impeccable adapt frontend/src/features/strategy-lab/StrategyLabPanel.tsx`

## Persona Red Flags

**Power Research Operator**: The density is useful, but the operator still has to scan multiple action zones to know whether a candidate should be handled from Experiment Rail, Candidate Board, Saved Experiment Table, or Paper Review. This creates small but repeated decision tax.

**Risk Reviewer**: Paper Review is much better now. The remaining red flag is that audit events are shown as a plain table below the action surface; for high-stakes review, the latest audit event and latest risk decision may deserve tighter visual association.

**First-Time Internal User**: The page communicates research-only and paper-only boundaries well, but A/B comparison, badge-check, archive, candidate, and review status require local product knowledge. They will not block the user, but they will slow confident first use.

## Minor Observations

- `Locked controls` is useful but could become verbose in terminal or draft states.
- The chart screen-reader summary is a meaningful improvement.
- `Loading candidates.` and `Loading experiments.` are clear but visually flat compared with the rest of the workflow.
- The product tone is calm and credible; avoid adding decorative motion or accent color here.

## Questions to Consider

- What is the one action the operator should take after finding a strong candidate: compare, mark candidate, create Paper Draft, or run Paper Review?
- Should Saved Experiment Table remain a full second action surface, or become a lower-priority audit/history table?
- Is mobile operation truly in scope, or should the interface explicitly optimize for desktop research and only remain readable on mobile?
