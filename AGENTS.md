# AQuantLens US Options Branch Workspace

1. Think Before Coding
Don't assume. Don't hide confusion. Surface tradeoffs.
Before implementing:
State your assumptions explicitly. If uncertain, ask.
If multiple interpretations exist, present them - don't pick silently.
If a simpler approach exists, say so. Push back when warranted.
If something is unclear, stop. Name what's confusing. Ask.
2. Simplicity First
Minimum code that solves the problem. Nothing speculative.
No features beyond what was asked.
No abstractions for single-use code.
No "flexibility" or "configurability" that wasn't requested.
No error handling for impossible scenarios.
If you write 200 lines and it could be 50, rewrite it.
Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.
3. Surgical Changes
Touch only what you must. Clean up only your own mess.
When editing existing code:
Don't "improve" adjacent code, comments, or formatting.
Don't refactor things that aren't broken.
Match existing style, even if you'd do it differently.
If you notice unrelated dead code, mention it - don't delete it.
When your changes create orphans:
Remove imports/variables/functions that YOUR changes made unused.
Don't remove pre-existing dead code unless asked.
The test: Every changed line should trace directly to the user's request.
4. Goal-Driven Execution
Define success criteria. Loop until verified.
Transform tasks into verifiable goals:
"Add validation" → "Write tests for invalid inputs, then make them pass"
"Fix the bug" → "Write a test that reproduces it, then make it pass"
"Refactor X" → "Ensure tests pass before and after"
For multi-step tasks, state a brief plan:
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.
## Project Identity

- This workspace contains the upstream `TradingAgents` framework cloned from `aliantech/TradingAgents`.
- Treat this repository as an independent **AQuantLens US/options branch**, focused on U.S. equities, SPX/SPY/QQQ, and selected U.S. options.
- Do not assume the existing AQuantLens main project architecture, data model, or China/A-share workflows should be reused directly.
- Use Yasin Brain `04-Projects/aquantlens` as background context only; this branch is allowed to diverge into a cleaner U.S.-market research and options framework.

## Required Context

Before important work, read:

1. `/Users/yasin/Workspace/Yasin AI OS/AGENTS.md`
2. `/Users/yasin/Workspace/Yasin AI OS/04-Projects/aquantlens/PROJECT.md`
3. `/Users/yasin/Workspace/Yasin AI OS/04-Projects/aquantlens/LOG.md` recent entries only
4. This file
5. `PROJECT.md`
6. Relevant docs under `docs/`

Do not read or print secrets, `.env` values, credential stores, browser sessions, private keys, or token caches.

## Execution Boundary

- Mac local work is for reading, editing, documentation, and lightweight static checks.
- Project services, dependency installation, Docker, tests, builds, and runtime verification should default to `ssh yasin-ubuntu` unless the user explicitly asks for Mac-local execution.
- If sandbox restrictions block an operation, treat it as an execution-environment issue first and use the approval flow.

## Branch and Upstream Policy

- `main` must stay aligned with upstream `aliantech/TradingAgents` and should not contain AQuantLens custom work.
- Custom U.S/options work happens on `aquantlens-us`.
- When upstream TradingAgents changes, update `main` first, review the upstream diff, then selectively adapt `aquantlens-us`.
- Do not blindly merge upstream into `aquantlens-us`; analyze compatibility, security fixes, model/provider updates, data-flow changes, and conflicts first.
- Prefer small selective commits on `aquantlens-us` that explain why an upstream change was adopted, modified, or skipped.
- If an upstream change touches shared TradingAgents core behavior, record the decision in project docs or Yasin Brain before large refactors.

## Phase 1 Scope

Current approved phase: **U.S. AI research workbench MVP**.

In scope:

- React/Vite/TypeScript frontend plan.
- FastAPI service wrapper plan.
- Chinese-first research reports with bilingual UI.
- PostgreSQL + TimescaleDB + Redis data layer plan.
- U.S. equities, SPX/SPY/QQQ, and selected liquid U.S. equity options.
- `lightweight-charts` charting plan.
- TradingAgents API-ization plan.

Out of scope for Phase 1:

- Live automated trading.
- Full backtesting engine.
- TradingView Advanced Charts or Trading Platform.
- Full OPRA tick/quote archival.
- Multi-user SaaS, billing, mobile apps, or public trading platform launch.

## Documentation Rules

- Keep public-facing README content product-oriented only.
- Internal rules, safety constraints, project decisions, and operational details belong in `AGENTS.md`, `PROJECT.md`, `docs/`, or Yasin Brain.
- Important changes should update local project docs and, when relevant, Yasin Brain with clear wording that this is the U.S/options branch rather than the existing AQuantLens mainline.
