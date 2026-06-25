"""Symbol normalization must apply on every yfinance path, not just price fetch.

Regression tests for #983 (instrument identity) and #984 (reflection returns):
a broker symbol like XAUUSD must resolve to the same Yahoo symbol (GC=F) that
the price path uses, so identity and realized-return lookups hit the right
instrument instead of failing/mismatching.
"""
import pandas as pd

import tradingagents.agents.utils.agent_utils as au
from tradingagents.graph.trading_graph import TradingAgentsGraph


def test_identity_lookup_normalizes_symbol(monkeypatch):
    seen = {}

    class FakeTicker:
        def __init__(self, symbol):
            seen["symbol"] = symbol

        @property
        def info(self):
            return {"longName": "Gold Futures", "quoteType": "FUTURE"}

    monkeypatch.setattr(au.yf, "Ticker", FakeTicker)
    au.resolve_instrument_identity.cache_clear()

    identity = au.resolve_instrument_identity("XAUUSD")

    assert seen["symbol"] == "GC=F"  # normalized, not the raw broker symbol
    assert identity.get("company_name") == "Gold Futures"


def test_fetch_returns_uses_finance_data_hub_symbol(monkeypatch):
    queried = []

    def fake_download_finance_data_hub_frame(symbol, start_date, end_date):
        queried.append(symbol)
        return pd.DataFrame({"Close": [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0]})

    monkeypatch.setattr(
        "tradingagents.dataflows.finance_data_hub._download_finance_data_hub_frame",
        fake_download_finance_data_hub_frame,
    )

    # _fetch_returns does not use ``self``; call unbound to avoid building the graph.
    raw, alpha, days = TradingAgentsGraph._fetch_returns(
        None, "XAUUSD", "2025-01-02", holding_days=5, benchmark="SPY"
    )

    assert queried[0] == "XAUUSD"
    assert queried[1] == "SPY"   # benchmark left as the canonical symbol
    assert raw is not None and days is not None
