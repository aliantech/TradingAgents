import copy
from datetime import datetime, timezone

import pytest

import tradingagents.dataflows.config as config_module
import tradingagents.default_config as default_config
from tradingagents.dataflows import direct_yahoo_chart
from tradingagents.dataflows.config import set_config
from tradingagents.dataflows.interface import route_to_vendor
from tradingagents.dataflows.stockstats_utils import load_ohlcv
from tradingagents.dataflows.symbol_utils import NoMarketDataError


def _timestamp(value: str) -> int:
    return int(datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def _chart_payload(date_value: str = "2026-06-18") -> dict:
    return {
        "chart": {
            "result": [
                {
                    "timestamp": [_timestamp(date_value)],
                    "indicators": {
                        "quote": [
                            {
                                "open": [548.25],
                                "high": [550.12],
                                "low": [546.8],
                                "close": [549.33],
                                "volume": [78123456],
                            }
                        ],
                        "adjclose": [{"adjclose": [549.33]}],
                    },
                }
            ],
            "error": None,
        }
    }


@pytest.fixture(autouse=True)
def reset_config():
    config_module._config = copy.deepcopy(default_config.DEFAULT_CONFIG)
    yield
    config_module._config = copy.deepcopy(default_config.DEFAULT_CONFIG)


@pytest.mark.unit
def test_direct_yahoo_chart_formats_ohlcv_csv(monkeypatch):
    seen_urls = []

    def fake_fetch_json(url):
        seen_urls.append(url)
        return _chart_payload()

    monkeypatch.setattr(direct_yahoo_chart, "_fetch_json", fake_fetch_json)

    result = direct_yahoo_chart.get_direct_yahoo_chart_data_online("SPY", "2026-06-18", "2026-06-18")

    assert "Stock data for SPY from 2026-06-18 to 2026-06-18" in result
    assert "Total records: 1" in result
    assert "Data source: Yahoo Finance chart endpoint" in result
    assert "2026-06-18,548.25,550.12,546.8,549.33,78123456,549.33" in result
    assert seen_urls
    assert "query1.finance.yahoo.com/v8/finance/chart/SPY" in seen_urls[0]
    assert "period1=" in seen_urls[0]
    assert "period2=" in seen_urls[0]


@pytest.mark.unit
def test_direct_yahoo_chart_falls_back_to_query2(monkeypatch):
    seen_urls = []

    def fake_fetch_json(url):
        seen_urls.append(url)
        if "query1.finance.yahoo.com" in url:
            raise OSError("query1 unavailable")
        return _chart_payload()

    monkeypatch.setattr(direct_yahoo_chart, "_fetch_json", fake_fetch_json)

    result = direct_yahoo_chart.get_direct_yahoo_chart_data_online("SPY", "2026-06-18", "2026-06-18")

    assert "Total records: 1" in result
    assert len(seen_urls) == 2
    assert "query1.finance.yahoo.com" in seen_urls[0]
    assert "query2.finance.yahoo.com" in seen_urls[1]


@pytest.mark.unit
def test_direct_yahoo_chart_empty_payload_raises_no_data(monkeypatch):
    monkeypatch.setattr(direct_yahoo_chart, "_fetch_json", lambda _url: {"chart": {"result": [], "error": None}})

    with pytest.raises(NoMarketDataError, match="no rows"):
        direct_yahoo_chart.get_direct_yahoo_chart_data_online("SPY", "2026-06-18", "2026-06-18")


@pytest.mark.unit
def test_vendor_router_accepts_direct_yahoo_chart(monkeypatch):
    monkeypatch.setattr(direct_yahoo_chart, "_fetch_json", lambda _url: _chart_payload())
    set_config({"data_vendors": {"core_stock_apis": "direct_yahoo_chart"}})

    result = route_to_vendor("get_stock_data", "SPY", "2026-06-18", "2026-06-18")

    assert "Data source: Yahoo Finance chart endpoint" in result


@pytest.mark.unit
def test_indicator_ohlcv_loader_uses_direct_yahoo_chart_when_configured(monkeypatch, tmp_path):
    def fail_if_yfinance_called(*_args, **_kwargs):
        raise AssertionError("yf.download should not be called")

    monkeypatch.setattr("tradingagents.dataflows.stockstats_utils.yf.download", fail_if_yfinance_called)
    monkeypatch.setattr(direct_yahoo_chart, "_fetch_json", lambda _url: _chart_payload())
    set_config(
        {
            "data_cache_dir": str(tmp_path),
            "tool_vendors": {"get_indicators": "direct_yahoo_chart"},
        }
    )

    frame = load_ohlcv("SPY", "2026-06-18")

    assert len(frame) == 1
    assert frame.iloc[0]["Close"] == 549.33
    assert list(tmp_path.glob("SPY-DirectYahooChart-data-*.csv"))
