---
target: frontend/src/app/App.tsx
total_score: 28
p0_count: 0
p1_count: 2
timestamp: 2026-06-20T07-02-33Z
slug: frontend-src-app-app-tsx
---
#### Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Many async states are visible, but Strategy Lab paper action eligibility is split across disabled buttons and hidden status logic. |
| 2 | Match System / Real World | 3 | Research-only and paper-only language is present; the paper submit cluster still needs stronger simulation framing. |
| 3 | User Control and Freedom | 3 | Refresh, cancel, archive, duplicate, compare, and reject paths exist; high-stakes paper controls need clearer recovery/sequence. |
| 4 | Consistency and Standards | 3 | Shared shadcn controls are mostly consistent, with some native selects and repeated local action clusters. |
| 5 | Error Prevention | 3 | Buttons are disabled for invalid paper states, but the UI does not always explain why the next step is blocked. |
| 6 | Recognition Rather Than Recall | 3 | Navigation and status labels are recognizable, though the operator must remember the paper workflow order. |
| 7 | Flexibility and Efficiency | 3 | Dense expert flows, filters, comparison actions, and saved experiments support repeat use; keyboard shortcuts are not visible. |
| 8 | Aesthetic and Minimalist Design | 2 | The workbench is credible but often exposes many peer controls at once, flattening priority. |
| 9 | Error Recovery | 3 | Error alerts exist for major API calls, but several empty/loading states are plain text rather than guided recovery. |
| 10 | Help and Documentation | 2 | Inline explanations exist, but there is little procedural guidance around paper review and risk-gated submit. |
| **Total** | | **28/40** | **Solid product foundation; needs hierarchy and workflow hardening.** |

#### Anti-Patterns Verdict

**LLM assessment:** The interface does not read as generic AI output in the obvious visual sense. It uses a restrained product palette, standard controls, real operational nouns, and avoids hero-metric theater. The main slop risk is structural: repeated card/table/action clusters make different decisions feel equally important, especially in Strategy Lab.

**Deterministic scan:** `detect.mjs --json frontend/src/app/App.tsx` returned `[]`. After DESIGN.md captured chart slate tokens, `detect.mjs --json frontend/src/features/strategy-lab/StrategyLabPanel.tsx` also returned `[]`.

**Visual overlays:** Browser overlay inspection was not run because this Codex session exposes only limited tab controls and no reliable mutable page-evaluation surface. No user-visible overlay is available; fallback signal is source review plus deterministic CLI scan.

#### Overall Impression

AQuantLens already feels like a serious internal workbench. The strongest next move is not a visual redesign; it is tightening high-stakes workflow hierarchy so the operator always knows which state they are in, why an action is blocked, and what the next paper-only step is.

#### What's Working

- The app uses a consistent product shell with familiar nav, lucide icons, shadcn controls, and restrained OKLCH tokens.
- The Strategy Lab keeps live/broker execution out of the UI and uses research_only / paper-only wording in important places.
- Dense data surfaces are appropriate for the audience: tables, filters, saved experiments, comparison, and audit trail all support repeat research work.

#### Priority Issues

**[P1] Paper Review action sequence is visually under-specified**  
**Why it matters:** RiskGuard, approval, rejection, submit, and cancel are all presented as a vertical button stack. The disabled states encode business rules, but the operator has to infer the workflow order.  
**Fix:** Add an explicit paper-only status summary, next-step guidance, and grouped controls: pre-submit review actions separate from final paper simulation actions.  
**Suggested command:** `$impeccable polish frontend/src/features/strategy-lab/StrategyLabPanel.tsx`

**[P1] Disabled paper actions do not explain their blockers**  
**Why it matters:** A disabled "Approve Paper" or "Paper Submit" is correct, but high-stakes workflows need to say whether the blocker is missing RiskGuard pass, not yet approved, filled, cancelled, or loading.  
**Fix:** Surface a compact eligibility note beside the action cluster.  
**Suggested command:** `$impeccable harden frontend/src/features/strategy-lab/StrategyLabPanel.tsx`

**[P2] Main workbench hierarchy is dense enough that priority flattens**  
**Why it matters:** The product is expert-facing, but dashboard, settings, runs, strategy, and market views share many card/table patterns. Without stronger section-level hierarchy, every panel asks for equal attention.  
**Fix:** Use clearer section grouping, tighter action columns, and more deliberate empty/loading copy.  
**Suggested command:** `$impeccable layout frontend/src/app/App.tsx`

**[P2] Mixed shared components and native controls create mild drift**  
**Why it matters:** Native selects inside otherwise shadcn-style forms look slightly less controlled and make future styling less predictable.  
**Fix:** Replace native selects incrementally with the existing shared Select where the surrounding form already uses shared inputs.  
**Suggested command:** `$impeccable polish frontend/src/app/App.tsx`

#### Persona Red Flags

**Power Operator:** Can scan tables and repeat workflows quickly, but must infer the paper review state machine from disabled buttons. This creates avoidable friction during repeated paper candidate evaluation.

**Risk-Conscious Reviewer:** Sees paper-only copy, but the final "Paper Submit" button needs stronger context that it is local simulation only and gated by human approval.

**First-Time Internal User:** Understands the navigation labels, but the Strategy Lab contains enough panels that "what do I do next?" is not always obvious after selecting a candidate.

#### Minor Observations

- Empty states are mostly plain text. They should often teach the next action.
- Native select styling is acceptable but not as integrated as the shared shadcn primitives.
- The newly documented chart slate colors should stay in DESIGN.md to prevent false detector drift.

#### Questions to Consider

- Should Strategy Lab teach the paper workflow as a sequence, or assume the operator already knows it?
- Is "Paper Submit" too terse for a high-stakes simulation action?
- Which surfaces are flagship quality now: Strategy Lab only, or the entire workbench shell?
