from datetime import UTC, date, datetime

from app.market_data.finance_data_hub import FinanceDataHubClient


class FakeTransport:
    def __init__(self, payload):
        self.payload = payload
        self.calls: list[str] = []

    def get_json(self, url: str):
        self.calls.append(url)
        if isinstance(self.payload, dict) and url in self.payload:
            return self.payload[url]
        return self.payload


def test_finance_data_hub_client_reads_asset_bars():
    transport = FakeTransport(
        {
            "http://hub.test/assets/SPY": {
                "asset_id": "asset-spy",
                "symbol": "SPY",
            },
            "http://hub.test/assets/asset-spy/bars?timeframe=1d&start=2026-06-17&end=2026-06-17": [
                {
                    "symbol": "SPY",
                    "timeframe": "1d",
                    "timestamp": "2026-06-17T00:00:00Z",
                    "open": "550.0",
                    "high": "553.0",
                    "low": "549.5",
                    "close": "552.2",
                    "volume": "90000000.00000000",
                    "source": "finance_data_hub",
                }
            ],
        }
    )
    client = FinanceDataHubClient("http://hub.test", transport=transport)

    bars = client.list_bars(symbol="spy", timeframe="1d", start=date(2026, 6, 17), end=date(2026, 6, 17))

    assert len(bars) == 1
    assert bars[0].symbol == "SPY"
    assert bars[0].timestamp == datetime(2026, 6, 17, tzinfo=UTC)
    assert bars[0].close == 552.2
    assert bars[0].volume == 90000000
    assert transport.calls == [
        "http://hub.test/assets/SPY",
        "http://hub.test/assets/asset-spy/bars?timeframe=1d&start=2026-06-17&end=2026-06-17",
    ]


def test_finance_data_hub_client_reads_asset_id_from_wrapped_asset_response():
    transport = FakeTransport(
        {
            "http://hub.test/assets/SPX": {"asset": {"asset_id": "asset-spx"}},
            "http://hub.test/assets/asset-spx/bars?timeframe=1d": [],
        }
    )
    client = FinanceDataHubClient("http://hub.test", transport=transport)

    bars = client.list_bars(symbol="spx", timeframe="1d")

    assert bars == []
    assert transport.calls == [
        "http://hub.test/assets/SPX",
        "http://hub.test/assets/asset-spx/bars?timeframe=1d",
    ]


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


def test_finance_data_hub_client_reads_option_contracts():
    transport = FakeTransport(
        {
            "contracts": [
                {
                    "underlying_symbol": "SPY",
                    "provider_symbol": "O:SPY260625C00726000",
                    "occ_symbol": "SPY260625C00726000",
                    "expiration_date": "2026-06-25",
                    "expiration_type": "weekly",
                    "strike": "726.00000000",
                    "right": "call",
                    "exercise_style": "american",
                    "source": "option_contracts",
                }
            ]
        }
    )
    client = FinanceDataHubClient("http://hub.test", transport=transport)

    contracts = client.list_option_contracts(underlying_symbol="spy", expiry=date(2026, 6, 25))

    assert len(contracts) == 1
    assert contracts[0].option_symbol == "O:SPY260625C00726000"
    assert contracts[0].underlying_symbol == "SPY"
    assert contracts[0].expiry == date(2026, 6, 25)
    assert contracts[0].strike == 726.0
    assert contracts[0].option_type == "call"
    assert contracts[0].source == "option_contracts"
    assert transport.calls == [
        "http://hub.test/options/contracts?underlying_symbol=SPY&limit=1000&expiration_date=2026-06-25"
    ]
