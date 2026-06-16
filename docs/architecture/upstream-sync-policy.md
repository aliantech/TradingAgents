# Upstream Sync Policy

## Purpose

Keep the repository connected to upstream TradingAgents while preserving a clean independent line for the AQuantLens U.S/options product.

## Branch Roles

- `main`: tracks upstream `aliantech/TradingAgents`.
- `aquanlens-us`: active AQuantLens U.S/options product branch.

## Rules

1. Do not develop AQuantLens product features on `main`.
2. Pull upstream TradingAgents changes into `main` first.
3. Review upstream changes before applying anything to `aquanlens-us`.
4. Apply upstream work selectively through small commits, cherry-picks, or manual ports.
5. Record important adoption/skip decisions when upstream changes affect architecture, data flows, security, model providers, report generation, or TradingAgents core behavior.

## Review Checklist

For each upstream update, check:

- Security fixes.
- Model/provider catalog updates.
- LangGraph or agent orchestration changes.
- Data vendor or market-data behavior changes.
- Prompt/report behavior changes.
- CLI and package structure changes.
- Breaking dependency updates.
- Tests that cover shared behavior.

## Adaptation Policy

Adopt upstream changes when they:

- Fix security or correctness issues.
- Improve model/provider coverage.
- Improve structured output reliability.
- Improve TradingAgents core stability.
- Reduce maintenance burden without harming branch goals.

Rewrite or skip upstream changes when they:

- Conflict with the U.S/options-first data model.
- Make Chinese-first reporting harder.
- Add assumptions tied to another market or workflow.
- Increase dependency or runtime complexity without clear benefit.
- Interfere with the planned FastAPI, React/Vite, TimescaleDB, Redis architecture.

## Expected Flow

```text
Switch to main
-> pull upstream TradingAgents
-> inspect commits and diff
-> switch to aquanlens-us
-> selectively port useful changes
-> run targeted verification
-> document important decisions
```

