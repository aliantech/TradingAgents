# Phase 4 Roadmap

## Objective

Phase 4 turns the Strategy Lab from a live preview surface into a research experiment workbench.

The goal is to let a user save, revisit, compare, and eventually graduate research-only strategy experiments without adding broker execution, live trading authority, or AI-directed order placement.

## Entry State

Phase 3 completed:

- Research Agent Gateway.
- Async research job contract.
- MCP thin wrapper over `/api/agent/v1`.
- WYSIWYG SignalStrategy research lab with live preview, deterministic research backtest, chart overlay, and report-linked notes.

Reference completion audit: `docs/roadmap/phase-3-completion-audit.md`.

## Slice 1: Strategy Experiment Persistence

Status: implemented and validated on 2026-06-19.

Implemented:

- `strategy_experiments` persistence model and SQL schema.
- `POST /api/strategy-lab/experiments` saves a research-only Strategy Lab preview snapshot.
- `GET /api/strategy-lab/experiments` lists recent experiments, optionally filtered by symbol.
- `GET /api/strategy-lab/experiments/{experiment_id}` opens a saved experiment.
- `POST /api/strategy-lab/experiments/{experiment_id}/duplicate` clones an experiment for iteration.
- Frontend Strategy Lab history panel lists saved experiments with windows, final equity, creation time, open, and duplicate actions.
- Opening a saved experiment restores its parameters and preview snapshot while preserving WYSIWYG live editing afterward.
- Manual parameter edits clear the active saved-experiment state and refresh the right-side preview.

Out of scope:

- Strategy execution.
- Broker adapters.
- Paper trading.
- Full backtest engine.
- Optimization sweeps.
- Multi-user experiment sharing.

## Next Slices

### Slice 2: Experiment Comparison

Status: implemented and validated on 2026-06-19.

Implemented:

- `GET /api/strategy-lab/experiments/compare` compares two saved Strategy Lab experiments.
- The compare endpoint requires both experiments to exist and share the same symbol.
- The response returns A/B titles, parameters, final equity, return, trade count, marker count, signal count, metric deltas, and per-parameter changed status.
- Frontend Strategy Lab history rows now include A/B comparison selectors.
- The comparison panel displays A/B experiment titles, final equity delta, return delta, trade delta, marker delta, signal delta, and changed/same parameter rows.

Out of scope:

- Cross-symbol comparison.
- Ranking or optimization.
- Statistical significance testing.
- Any paper/live execution decisioning.

### Slice 3: Strategy Catalog Boundary

Planned:

- Register Strategy Lab strategies through a typed catalog rather than hard-coding SignalStrategy-only frontend assumptions.
- Keep each strategy contract deterministic and research-only.
- Prepare a boundary for future event-driven strategies without exposing execution.

## Validation Evidence

Slice 1 backend validation on 2026-06-19:

```bash
cd /home/yasin/workspace/TradingAgents/backend
. .venv/bin/activate
pytest -q tests/test_strategy_lab_contracts.py tests/test_strategy_lab_api.py tests/test_strategy_lab_experiments_api.py --tb=short
```

Result:

```text
7 passed in 0.66s
```

Frontend validation on 2026-06-19:

```bash
cd /home/yasin/workspace/TradingAgents/frontend
npm run build
```

Result:

```text
✓ built in 413ms
```

Rendered WYSIWYG persistence check:

- Opened `http://127.0.0.1:5173/#strategy` against the updated backend API.
- Saved the current `SPY 2/3 SignalStrategy` preview.
- Changed Fast Window from `2` to `5`, which kept Slow Window valid at `5` and updated the right-side preview to `Markers 0 / Trades 0 / Final $10,000`.
- Opened the saved experiment and confirmed parameters restored to `2 / 3` and the preview restored to `Markers 34 / Trades 17 / Final $10,040.95`.
- Duplicated the saved experiment and confirmed the copied experiment appeared in history and became the active opened experiment.
- Browser console had no errors during the rendered check.

Slice 2 backend validation on 2026-06-19:

```bash
cd /home/yasin/workspace/TradingAgents/backend
. .venv/bin/activate
pytest -q tests/test_strategy_lab_contracts.py tests/test_strategy_lab_api.py tests/test_strategy_lab_experiments_api.py --tb=short
```

Result:

```text
8 passed in 0.63s
```

Slice 2 frontend validation on 2026-06-19:

```bash
cd /home/yasin/workspace/TradingAgents/frontend
npm run build
```

Result:

```text
✓ built in 360ms
```

Rendered comparison check:

- Opened `http://127.0.0.1:5173/#strategy` against the updated backend compare API.
- Selected `SPY MA baseline` as comparison A and `SPY MA flat` as comparison B.
- Confirmed the comparison panel displayed `Final Delta +$3`, `Return Delta +0.03%`, `Trades Delta -1`, `Markers Delta -2`, and `Signals Delta 0`.
- Confirmed parameter rows showed `fast_window 2 -> 5 Changed` and `slow_window 3 -> 5 Changed`.
- Browser console had no errors during the rendered check.
