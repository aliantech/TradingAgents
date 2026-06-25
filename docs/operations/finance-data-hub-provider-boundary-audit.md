# Finance Data Hub Provider Boundary Audit

Date: 2026-06-26

## Scope

TradingAgents should not directly access Polygon/Massive, Futu, or IBKR APIs for market or options data. Those vendor integrations belong in Finance Data Hub.

TradingAgents remains a read-only consumer of normalized data exposed by Finance Data Hub.

## Current Result

No active TradingAgents runtime code, dependency, configuration, or script directly imports or calls Futu/OpenD, IBKR/TWS, `ibapi`, or `ib_insync`.

The only remaining Futu/IBKR references are historical planning/search-audit text in docs. Those do not create runtime API access.

## Verification

Searches run from the TradingAgents workspace:

- `rg -n -i "\\b(futu|futuapi|opend|openapi|ibkr|ibapi|ib_insync|interactive brokers|ib gateway|tws)\\b" . --glob '!frontend/node_modules/**'`
- `rg -n -i "futu|ibkr|ibapi|ib_insync|interactive brokers|ib gateway|tws|opend" pyproject.toml requirements.txt backend frontend scripts tradingagents --glob '!frontend/node_modules/**'`

No active runtime API integration was found.
