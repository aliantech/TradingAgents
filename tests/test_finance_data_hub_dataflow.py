import copy

import pytest

import tradingagents.dataflows.config as config_module
import tradingagents.default_config as default_config
from tradingagents.dataflows import finance_data_hub
from tradingagents.dataflows.config import set_config
from tradingagents.dataflows.interface import route_to_vendor
from tradingagents.dataflows.stockstats_utils import load_ohlcv
from tradingagents.dataflows.symbol_utils import NoMarketDataError


@pytest.fixture(autouse=True)
def reset_config():
    config_module._config = copy.deepcopy(default_config.DEFAULT_CONFIG)
    yield
    config_module._config = copy.deepcopy(default_config.DEFAULT_CONFIG)


def _bar(timestamp: str = "2026-06-18T20:00:00Z") -> dict:
    return {
        "timestamp": timestamp,
        "open": "548.25",
        "high": "550.12",
        "low": "546.80",
        "close": "549.33",
        "volume": "78123456",
    }


@pytest.mark.unit
def test_finance_data_hub_formats_ohlcv_csv(monkeypatch):
    seen_urls = []

    def fake_fetch_json(url):
        seen_urls.append(url)
        if url == "http://hub.test/assets/SPY":
            return {"asset": {"asset_id": "asset-spy"}}
        if url == "http://hub.test/assets/asset-spy/bars?timeframe=1d&start=2026-06-18&end=2026-06-18":
            return [_bar()]
        raise AssertionError(f"unexpected URL: {url}")

    monkeypatch.setattr(finance_data_hub, "_fetch_json", fake_fetch_json)
    set_config({"finance_data_hub_base_url": "http://hub.test"})

    result = finance_data_hub.get_finance_data_hub_data_online("SPY", "2026-06-18", "2026-06-18")

    assert "Stock data for SPY from 2026-06-18 to 2026-06-18" in result
    assert "Total records: 1" in result
    assert "Data source: Finance Data Hub" in result
    assert "2026-06-18,548.25,550.12,546.8,549.33,78123456,549.33" in result
    assert seen_urls == [
        "http://hub.test/assets/SPY",
        "http://hub.test/assets/asset-spy/bars?timeframe=1d&start=2026-06-18&end=2026-06-18",
    ]


@pytest.mark.unit
def test_finance_data_hub_empty_payload_raises_no_data(monkeypatch):
    def fake_fetch_json(url):
        if url == "http://hub.test/assets/SPY":
            return {"asset_id": "asset-spy"}
        return []

    monkeypatch.setattr(finance_data_hub, "_fetch_json", fake_fetch_json)
    set_config({"finance_data_hub_base_url": "http://hub.test"})

    with pytest.raises(NoMarketDataError, match="no rows"):
        finance_data_hub.get_finance_data_hub_data_online("SPY", "2026-06-18", "2026-06-18")


@pytest.mark.unit
def test_vendor_router_accepts_finance_data_hub(monkeypatch):
    def fake_fetch_json(url):
        if url == "http://hub.test/assets/SPY":
            return {"asset_id": "asset-spy"}
        return [_bar()]

    monkeypatch.setattr(finance_data_hub, "_fetch_json", fake_fetch_json)
    set_config(
        {
            "finance_data_hub_base_url": "http://hub.test",
            "data_vendors": {"core_stock_apis": "finance_data_hub"},
        }
    )

    result = route_to_vendor("get_stock_data", "SPY", "2026-06-18", "2026-06-18")

    assert "Data source: Finance Data Hub" in result


@pytest.mark.unit
def test_indicator_ohlcv_loader_uses_finance_data_hub_when_configured(monkeypatch, tmp_path):
    def fail_if_yfinance_called(*_args, **_kwargs):
        raise AssertionError("yf.download should not be called")

    def fake_download_finance_data_hub_frame(symbol, start_date, end_date):
        assert symbol == "SPY"
        return finance_data_hub._bars_to_frame([_bar("2026-06-18T20:00:00Z")])

    monkeypatch.setattr("tradingagents.dataflows.stockstats_utils.yf.download", fail_if_yfinance_called)
    monkeypatch.setattr(finance_data_hub, "_download_finance_data_hub_frame", fake_download_finance_data_hub_frame)
    set_config(
        {
            "data_cache_dir": str(tmp_path),
            "tool_vendors": {"get_indicators": "finance_data_hub"},
        }
    )

    frame = load_ohlcv("SPY", "2026-06-18")

    assert len(frame) == 1
    assert frame.iloc[0]["Close"] == 549.33
    assert list(tmp_path.glob("SPY-FinanceDataHub-data-*.csv"))
