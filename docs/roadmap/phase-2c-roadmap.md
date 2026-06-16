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

## Verification

Ubuntu backend verification:

```bash
pytest tests/test_options_repository.py -q
pytest -q
```

Results:

- Targeted options repository tests: `2 passed`.
- Full backend suite: `75 passed`.

## Next Slice

- Connect the existing options API layer to `OptionRepository`.
- Add deterministic sample option-chain seed data for SPY and SPX-style contracts.
- Add API tests for contract and chain snapshot responses.
- Add frontend option-chain panel skeleton under `frontend`.
- Keep provider-specific Polygon/Massive option-chain ingestion as the following slice after the API/UI boundary is stable.
