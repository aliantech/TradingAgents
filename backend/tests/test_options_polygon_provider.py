from datetime import UTC, date, datetime
from urllib.parse import parse_qs, urlparse

from app.options.polygon_provider import PolygonOptionsProvider


class FakeOptionsTransport:
    def __init__(self, response: dict) -> None:
        self.response = response
        self.calls: list[str] = []

    def get_json(self, url: str) -> dict:
        self.calls.append(url)
        return self.response


def test_polygon_options_provider_converts_chain_snapshot_payload():
    transport = FakeOptionsTransport(
        {
            "results": [
                {
                    "details": {
                        "ticker": "O:SPX240621C05500000",
                        "underlying_ticker": "SPX",
                        "expiration_date": "2024-06-21",
                        "strike_price": 5500,
                        "contract_type": "call",
                        "exercise_style": "european",
                    },
                    "greeks": {"delta": 0.42, "gamma": 0.018, "theta": -0.09, "vega": 0.21},
                    "implied_volatility": 0.19,
                    "last_quote": {"bid": 4.2, "ask": 4.4, "last_updated": 1718631000000000000},
                    "last_trade": {"price": 4.3},
                    "open_interest": 1200,
                    "day": {"volume": 220},
                }
            ]
        }
    )
    provider = PolygonOptionsProvider(api_key="test-key", transport=transport)

    records = provider.fetch_chain_snapshot("spx", expiry=date(2024, 6, 21), limit=25)

    assert len(records) == 1
    assert records[0].contract.option_symbol == "O:SPX240621C05500000"
    assert records[0].contract.underlying_symbol == "SPX"
    assert records[0].contract.expiry == date(2024, 6, 21)
    assert records[0].contract.strike == 5500
    assert records[0].contract.option_type == "call"
    assert records[0].contract.exercise_style == "european"
    assert records[0].snapshot.timestamp == datetime(2024, 6, 17, 13, 30, tzinfo=UTC)
    assert records[0].snapshot.bid == 4.2
    assert records[0].snapshot.ask == 4.4
    assert records[0].snapshot.last == 4.3
    assert records[0].snapshot.volume == 220
    assert records[0].snapshot.open_interest == 1200
    assert records[0].snapshot.implied_volatility == 0.19
    assert records[0].snapshot.source == "polygon"

    parsed = urlparse(transport.calls[0])
    query = parse_qs(parsed.query)
    assert parsed.path == "/v3/snapshot/options/SPX"
    assert query["expiration_date"] == ["2024-06-21"]
    assert query["limit"] == ["25"]
    assert query["apiKey"] == ["test-key"]
