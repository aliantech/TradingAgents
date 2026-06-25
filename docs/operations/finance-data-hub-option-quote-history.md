# Finance Data Hub Option Quote History

Date: 2026-06-26

## Scope

TradingAgents no longer reads option quote history directly from Polygon/Massive. Selected option history is read through Finance Data Hub.

This slice keeps option OHLC bars separate from quote history. Finance Data Hub currently exposes usable option quote history through `/options/quotes/history`, while selected option OHLC bars can remain empty when Hub has no bar contract for the option symbol.

## Implementation

- Added `FinanceDataHubClient.list_option_quote_history()`.
- Added `GET /api/options/quotes/history`.
- Added a selected-contract Quote History panel in the options workbench.
- Kept `GET /api/options/bars` and the Option Bars panel unchanged.

## Verification

Ubuntu verification workspace: `/home/yasin/workspace/TradingAgents-aquantlens-us-latest`.

- `python -m pytest backend/tests/test_finance_data_hub_client.py backend/tests/test_options_api.py -q` passed: `14 passed`.
- Finance Data Hub live smoke returned `quotes 3 O:SPY260625C00726000 7.615 option_quotes_history`.
- `npm run build` passed in `frontend`.
- Browser smoke on `http://127.0.0.1:5174/#options` selected `O:SPY260625C00726000` and showed `option_quotes_history · 3 quotes`; browser console errors were empty.
