# AQuantLens US Options Branch Workspace

## Project Identity

- This workspace contains the upstream `TradingAgents` framework cloned from `aliantech/TradingAgents`.
- Treat this repository as an independent **AQuantLens US/options branch**, focused on U.S. equities, SPX/SPY/QQQ, and selected U.S. options.
- Do not assume the existing AQuantLens main project architecture, data model, or China/A-share workflows should be reused directly.
- Use Yasin Brain `04-Projects/aquantlens` as background context only; this branch is allowed to diverge into a cleaner U.S.-market research and options framework.

## Required Context

Before important work, read:

1. `/Users/yasin/Documents/Yasin AI OS/AGENTS.md`
2. `/Users/yasin/Documents/Yasin AI OS/04-Projects/aquantlens/PROJECT.md`
3. `/Users/yasin/Documents/Yasin AI OS/04-Projects/aquantlens/LOG.md` recent entries only
4. This file
5. `PROJECT.md`
6. Relevant docs under `docs/`

Do not read or print secrets, `.env` values, credential stores, browser sessions, private keys, or token caches.

## Execution Boundary

- Mac local work is for reading, editing, documentation, and lightweight static checks.
- Project services, dependency installation, Docker, tests, builds, and runtime verification should default to `ssh yasin-ubuntu` unless the user explicitly asks for Mac-local execution.
- If sandbox restrictions block an operation, treat it as an execution-environment issue first and use the approval flow.

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
