from datetime import datetime, timezone

from app.market_data.schemas import MarketBar
from app.realtime.cache_keys import MARKET_EVENTS_STREAM
from app.realtime.market_data_publisher import RedisMarketDataPublisher


class FakeRedisClient:
    def __init__(self) -> None:
        self.set_calls = []
        self.xadd_calls = []

    def set(self, name: str, value: str, ex: int | None = None) -> None:
        self.set_calls.append({"name": name, "value": value, "ex": ex})

    def xadd(self, name: str, fields: dict[str, str]) -> None:
        self.xadd_calls.append({"name": name, "fields": fields})


def test_redis_market_data_publisher_writes_latest_and_stream_event():
    client = FakeRedisClient()
    publisher = RedisMarketDataPublisher(client, ttl_seconds=60)
    bar = MarketBar(
        symbol="spy",
        timeframe="1m",
        timestamp=datetime(2026, 6, 17, 13, 30, tzinfo=timezone.utc),
        open=550.0,
        high=551.0,
        low=549.5,
        close=550.5,
        volume=1_000_000,
        source="unit-test",
    )

    publisher.publish_bar(bar)

    assert client.set_calls[0]["name"] == "latest:SPY"
    assert client.set_calls[0]["ex"] == 60
    assert '"symbol": "SPY"' in client.set_calls[0]["value"]
    assert client.xadd_calls[0]["name"] == MARKET_EVENTS_STREAM
    assert client.xadd_calls[0]["fields"]["event_type"] == "bar"
    assert client.xadd_calls[0]["fields"]["symbol"] == "SPY"
