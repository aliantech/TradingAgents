# Phase 2C Roadmap

## Objective

Build the U.S. options data foundation for AQuantLens US so the platform can store selected SPX/SPY/QQQ and liquid U.S. equity option-chain data before adding option analytics, quant models, or any trading workflow.

Phase 2C remains a data and research layer. It does not add broker order placement, AI trading authority, or live execution.

## Scope

- Option contract metadata for selected underlyings.
- Option-chain snapshot storage for bid, ask, last, volume, open interest, implied volatility, and Greeks.
- Provider-neutral repository interfaces before provider-specific adapters grow larger.
- API endpoints that expose option contracts and chain snapshots to the frontend.
- Frontend option-chain views with Chinese-first labels and English professional terms where appropriate.
- Future compatibility with option bars, volatility surfaces, strategy builders, and backtesting.

## Completed in First Slice

- Added `option_contracts` ORM model.
- Added `option_snapshots` ORM model.
- Added `OptionRepository` with:
  - contract upsert;
  - contract listing by underlying and expiry;
  - snapshot upsert;
  - chain snapshot listing by underlying and expiry.
- Added repository tests covering idempotent contract writes and idempotent snapshot updates.

## Completed in Second Slice

- Added a guarded options entitlement live smoke module:
  - checks contracts endpoint for each underlying;
  - checks option-chain snapshot endpoint for each underlying;
  - defaults to `SPY,SPX` so ETF options and index options are tested together;
  - supports configurable timeout and retry for slow option-chain responses;
  - returns JSON with `succeeded`, `partial`, `failed`, or `not_ready`.
- Added `scripts/phase2c_options_live_smoke.sh`.
- The shell script does not read `.env`, print environment variables, or expose the API key.
- Added tests for the smoke module and shell-script safety boundary.

## Verification

Ubuntu backend verification:

```bash
pytest tests/test_options_repository.py -q
pytest tests/test_options_live_smoke.py tests/test_phase2c_options_live_smoke_script.py -q
pytest -q
```

Results:

- Targeted options repository tests: `2 passed`.
- Targeted options live smoke tests: `4 passed`.
- Timeout/retry options live smoke tests: `5 passed`.
- Full backend suite: `80 passed`.
- Guarded no-key smoke returns `status=not_ready` with missing `AQUANTLENS_POLYGON_API_KEY`.

## Live Entitlement Check

Run this in a runtime shell/session where `AQUANTLENS_POLYGON_API_KEY` is already provided:

```bash
scripts/phase2c_options_live_smoke.sh
```

Optional custom underlyings:

```bash
scripts/phase2c_options_live_smoke.sh SPY,QQQ,SPX
```

For a slow index option-chain response, run SPX alone with a longer timeout:

```bash
scripts/phase2c_options_live_smoke.sh SPX 90 1
```

Interpretation:

- `SPY` success verifies ETF options access.
- `SPX` success verifies index options access.
- `partial` means the endpoint was reachable but one side returned an empty result.
- `failed` with HTTP 403 means the plan, ticker, or endpoint access needs entitlement review.
- `failed` with a read timeout is inconclusive; rerun the underlying alone with a longer timeout before judging entitlement.

Observed first live run:

- `SPY` contracts and chain snapshot succeeded.
- `SPX` did not return 403 or empty; the request timed out, so index-options entitlement remains inconclusive until a longer SPX-only check completes.

## WebSocket Note

Massive WebSocket docs describe Options streams as real-time OPRA trades, quotes, and aggregates. WebSocket ingestion is useful for future realtime cache/events, but Phase 2C should first validate REST entitlement and persistence because REST responses are easier to audit and replay.

## Next Slice

- Connect the existing options API layer to `OptionRepository`.
- Add deterministic sample option-chain seed data for SPY and SPX-style contracts.
- Add API tests for contract and chain snapshot responses.
- Add frontend option-chain panel skeleton under `frontend`.
- Keep provider-specific Polygon/Massive option-chain ingestion as the following slice after the API/UI boundary is stable.
