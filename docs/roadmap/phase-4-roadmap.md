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

Status: implemented and validated on 2026-06-19.

Implemented:

- Added `backend/app/strategy_lab/catalog.py` as the typed research-only strategy registry.
- Registered `ma-cross-research` with name, description, default parameters, and parameter schema.
- Added `GET /api/strategy-lab/strategies` for frontend catalog discovery.
- Preview requests now validate `strategy_id` against the catalog and reject unknown strategies.
- Frontend Strategy Lab loads the catalog and renders strategy name, id, description, and default parameters from the catalog.
- Saved experiment titles now use the catalog strategy name instead of a hard-coded SignalStrategy label.

Out of scope:

- Multiple strategy implementations.
- Event-driven strategy runtime.
- Strategy plugin loading.
- Paper or live execution.
- Broker adapters.

### Slice 4: Experiment Curation

Status: implemented and validated on 2026-06-19.

Implemented:

- Added research-only curation metadata to saved Strategy Lab experiments: tags, notes, and archived state.
- Added create-time tags and notes for saved experiments.
- Added `PATCH /api/strategy-lab/experiments/{experiment_id}` to update tags, notes, and archived state.
- `GET /api/strategy-lab/experiments` now hides archived experiments by default, can include archived rows, and can filter by tag.
- Duplicating an archived experiment creates an active copy while preserving tags and notes.
- Frontend Strategy Lab save controls now include tags and notes.
- Frontend experiment rail and saved experiment table render tags, notes, archived badges, archive/restore actions, archived visibility toggle, and tag filtering.

Out of scope:

- Ranking or optimization.
- Cross-symbol curation workflows.
- Multi-user sharing.
- Paper trading.
- Live execution.
- Broker adapters.

### Slice 5: Experiment Review Gate

Status: implemented and validated on 2026-06-19.

Implemented:

- Added research-only review metadata to saved Strategy Lab experiments: `review_status` and `review_checklist`.
- Review statuses are limited to `draft`, `reviewed`, `candidate`, and `rejected`.
- New experiments default to `draft` with an empty review checklist.
- `PATCH /api/strategy-lab/experiments/{experiment_id}` can update review status and checklist fields.
- `GET /api/strategy-lab/experiments` can filter by review status while preserving existing symbol, tag, and archived filters.
- Duplicated experiments restart as `draft` so a copied experiment must pass review independently.
- Frontend Strategy Lab now renders review status in workflow tiles, experiment rail cards, and saved experiment metadata.
- Frontend experiment rail and saved experiment table include review actions for reviewed, candidate, and rejected states.
- Frontend experiment rail includes a review-status filter.

Out of scope:

- Paper trading promotion.
- Live trading approval.
- Broker adapters.
- Order intents.
- Automated ranking or optimization.
- Statistical significance gates.

### Slice 6: Candidate Review Board

Status: implemented and validated on 2026-06-20.

Implemented:

- Added a research-only candidate board endpoint: `GET /api/strategy-lab/experiments/candidates`.
- Candidate board returns only active, non-archived experiments with `review_status=candidate`.
- Candidate board supports filtering by symbol, strategy id, and tag.
- Candidate board supports sorting by created time or return percentage.
- Candidate rows expose saved experiment identifiers, strategy, symbol, final equity, return percentage, trade count, marker count, signal count, tags, checklist, and creation time.
- Frontend Strategy Lab now renders a Candidate Review Board from the candidate endpoint.
- Candidate board supports tag filtering and return/created sorting.
- Candidate board actions can open a candidate, use it as comparison A/B, reject it, or archive it.

Out of scope:

- Paper trading promotion.
- Live trading approval.
- Broker adapters.
- Order intents.
- Automated optimization.
- Statistical significance ranking.

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

Slice 3 backend validation on 2026-06-19:

```bash
cd /home/yasin/workspace/TradingAgents/backend
. .venv/bin/activate
pytest -q tests/test_strategy_lab_contracts.py tests/test_strategy_lab_api.py tests/test_strategy_lab_experiments_api.py --tb=short
```

Result:

```text
10 passed in 0.65s
```

Slice 3 frontend validation on 2026-06-19:

```bash
cd /home/yasin/workspace/TradingAgents/frontend
npm run build
```

Result:

```text
✓ built in 422ms
```

Rendered catalog check:

- Opened `http://127.0.0.1:5173/#strategy` against the updated backend catalog API.
- Confirmed Strategy Lab rendered `MA Cross Research`, `ma-cross-research`, and `Research-only moving average signal contract.` from the catalog.
- Confirmed default parameter inputs loaded as Fast Window `2`, Slow Window `3`, Initial Equity `10000`.
- Confirmed the right-side live preview still rendered `Markers 34 / Trades 17 / Final $10,040.95`.
- Saved the current experiment and confirmed the opened/history title used `SPY 2/3 MA Cross Research`.
- Browser console had no errors during the rendered check.

Slice 4 backend validation on 2026-06-19:

```bash
cd /tmp/tradingagents-slice4/backend
PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q tests/test_strategy_lab_contracts.py tests/test_strategy_lab_api.py tests/test_strategy_lab_experiments_api.py --tb=short
```

Result:

```text
11 passed in 1.55s
```

Full backend regression on 2026-06-19:

```bash
cd /tmp/tradingagents-slice4/backend
PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q --tb=short
```

Result:

```text
138 passed in 3.36s
```

Slice 4 frontend validation on 2026-06-19:

```bash
cd /tmp/tradingagents-slice4/frontend
ln -sfn /home/yasin/workspace/TradingAgents/frontend/node_modules node_modules
npm run build
```

Result:

```text
✓ built in 798ms
```

Slice 5 backend validation on 2026-06-19:

```bash
cd /tmp/tradingagents-slice4/backend
PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q tests/test_strategy_lab_contracts.py tests/test_strategy_lab_api.py tests/test_strategy_lab_experiments_api.py --tb=short
```

Result:

```text
12 passed in 1.30s
```

Full backend regression on 2026-06-19:

```bash
cd /tmp/tradingagents-slice4/backend
PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q --tb=short
```

Result:

```text
139 passed in 3.81s
```

Slice 5 frontend validation on 2026-06-19:

```bash
cd /tmp/tradingagents-slice4/frontend
npm run build
```

Result:

```text
✓ built in 430ms
```

Slice 6 backend validation on 2026-06-20:

```bash
cd /tmp/tradingagents-slice4/backend
PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q tests/test_strategy_lab_contracts.py tests/test_strategy_lab_api.py tests/test_strategy_lab_experiments_api.py --tb=short
```

Result:

```text
13 passed in 2.64s
```

Full backend regression on 2026-06-20:

```bash
cd /tmp/tradingagents-slice4/backend
PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q --tb=short
```

Result:

```text
140 passed in 5.03s
```

Slice 6 frontend validation on 2026-06-20:

```bash
cd /tmp/tradingagents-slice4/frontend
npm run build
```

Result:

```text
✓ built in 767ms
```
