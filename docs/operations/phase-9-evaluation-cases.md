# Phase 9 Evaluation Cases

Phase 9 Slice 2 defines a small repeatable case set for research-output evaluation.

The case set lives in `backend/app/research_evaluation/cases.py` and is versioned as `phase-9-slice-2-v1`.

## Scope

The built-in set covers:

- `SPY`: broad U.S. equity ETF macro/options read-through.
- `QQQ`: growth-heavy ETF technical setup.
- `AAPL`: mega-cap single-name research.
- `TSLA`: volatile single-name research.
- `SPX`: index-oriented macro/options read-through.

Each case fixes:

- Symbol.
- Asset type.
- Analysis date.
- Chinese-first report language.
- Analysis depth.
- Analyst set.
- Research template.
- Deterministic baseline provider and model.
- Baseline report-quality expectations.

## Extension Rules

When adding a case:

- Keep `case_id` unique and stable.
- Use uppercase symbols.
- Keep `language` as `zh` unless a later phase explicitly adds bilingual evaluation.
- Use deterministic provider/model defaults in automated tests.
- Add only non-secret metadata.
- Do not add provider API keys, `.env` loading, broker fields, live execution controls, scheduled provider calls, or automatic retries.
- Run `validate_evaluation_case_set()` through focused backend tests.

## Boundary

This case set does not call TradingAgents, providers, brokers, market-data APIs, or live execution systems by itself.

It only defines deterministic inputs and expectations so later evaluation and review workflows can compare outputs consistently.
