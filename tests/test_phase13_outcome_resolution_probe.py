import yfinance

from scripts.phase13_outcome_resolution_probe import run_probe
from tradingagents.graph.trading_graph import TradingAgentsGraph


def test_outcome_resolution_probe_reports_success(monkeypatch):
    monkeypatch.setattr(
        TradingAgentsGraph,
        "_fetch_returns",
        lambda self, symbol, trade_date, holding_days, benchmark: (0.06, 0.045, 5),
    )

    result = run_probe("NVDA", "2026-01-05", holding_days=5, benchmark="SPY", timeout_seconds=10)

    assert result["status"] == "succeeded"
    assert result["symbol"] == "NVDA"
    assert result["benchmark"] == "SPY"
    assert result["raw_return"] == 0.06
    assert result["alpha_return"] == 0.045
    assert result["actual_holding_days"] == 5
    assert result["yfinance_ticker_blocked"] is True


def test_outcome_resolution_probe_reports_no_data(monkeypatch):
    monkeypatch.setattr(
        TradingAgentsGraph,
        "_fetch_returns",
        lambda self, symbol, trade_date, holding_days, benchmark: (None, None, None),
    )

    result = run_probe("NVDA", "2026-01-05", holding_days=5, benchmark="SPY", timeout_seconds=10)

    assert result["status"] == "no_data"
    assert result["raw_return"] is None
    assert result["alpha_return"] is None
    assert result["actual_holding_days"] is None


def test_outcome_resolution_probe_blocks_yfinance_ticker(monkeypatch):
    def call_yfinance(self, symbol, trade_date, holding_days, benchmark):
        yfinance.Ticker(symbol)
        return (0.0, 0.0, 1)

    monkeypatch.setattr(TradingAgentsGraph, "_fetch_returns", call_yfinance)

    result = run_probe("NVDA", "2026-01-05", holding_days=5, benchmark="SPY", timeout_seconds=10)

    assert result["status"] == "failed"
    assert result["error_type"] == "YFinanceTickerBlocked"
    assert "disabled" in result["error_message"]
