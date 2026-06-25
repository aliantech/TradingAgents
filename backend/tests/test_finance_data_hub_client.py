from datetime import UTC, date, datetime

from app.market_data.finance_data_hub import FinanceDataHubClient


class FakeTransport:
    def __init__(self, payload):
        self.payload = payload
        self.calls: list[str] = []

    def get_json(self, url: str):
        self.calls.append(url)
        return self.payload


def test_finance_data_hub_client_reads_asset_bars():
    transport = FakeTransport(
        [
            {
                "symbol": "SPY",
                "timeframe": "1d",
                "timestamp": "2026-06-17T00:00:00Z",
                "open": "550.0",
                "high": "553.0",
                "low": "549.5",
                "close": "552.2",
                "volume": "90000000",
                "source": "finance_data_hub",
            }
        ]
    )
    client = FinanceDataHubClient("http://hub.test", transport=transport)

    bars = client.list_bars(symbol="spy", timeframe="1d", start=date(2026, 6, 17), end=date(2026, 6, 17))

    assert len(bars) == 1
    assert bars[0].symbol == "SPY"
    assert bars[0].timestamp == datetime(2026, 6, 17, tzinfo=UTC)
    assert bars[0].close == 552.2
    assert transport.calls == ["http://hub.test/assets/SPY/bars?timeframe=1d&start=2026-06-17&end=2026-06-17"]


def test_finance_data_hub_client_reads_option_latest_quotes():
    transport = FakeTransport(
        {
            "quotes": [
                {
                    "underlying_symbol": "SPY",
                    "provider_symbol": "O:SPY260116C00500000",
                    "expiration_date": "2026-01-16",
                    "provider_timestamp": "2026-01-16T14:30:00Z",
                    "bid": "4.1",
                    "ask": "4.3",
                    "mid": "4.2",
                    "volume": 100,
                    "open_interest": 1200,
                    "implied_volatility": "0.19",
                    "delta": "0.42",
                    "gamma": "0.018",
                    "theta": "-0.09",
                    "vega": "0.21",
                }
            ]
        }
    )
    client = FinanceDataHubClient("http://hub.test", transport=transport)

    snapshots = client.list_option_latest_quotes(underlying_symbol="spy", expiry=date(2026, 1, 16))

    assert len(snapshots) == 1
    assert snapshots[0].option_symbol == "O:SPY260116C00500000"
    assert snapshots[0].underlying_symbol == "SPY"
    assert snapshots[0].last == 4.2
    assert snapshots[0].source == "finance_data_hub"
    assert transport.calls == ["http://hub.test/options/quotes/latest/SPY?expiration_date=2026-01-16"]
