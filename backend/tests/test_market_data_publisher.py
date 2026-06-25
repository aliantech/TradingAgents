from datetime import datetime, timezone

from app.market_data.schemas import MarketBar
from app.realtime.cache_keys import MARKET_EVENTS_STREAM
from app.realtime.market_data_publisher import RedisMarketDataPublisher, create_market_data_publisher


class FakeRedisClient:
    def __init__(self) -> None:
        self.set_calls = []
        self.xadd_calls = []

    def set(self, name: str, value: str, ex: int | None = None) -> None:
        self.set_calls.append({"name": name, "value": value, "ex": ex})

    def xadd(self, name: str, fields: dict[str, str]) -> None:
        self.xadd_calls.append({"name": name, "fields": fields})


class FakeRedis:
    instances = []

    @classmethod
    def from_url(cls, url: str):
        instance = cls()
        instance.url = url
        cls.instances.append(instance)
        return instance


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


def test_create_market_data_publisher_returns_none_when_disabled():
    publisher = create_market_data_publisher(enabled=False, redis_url="redis://localhost:6379/0")

    assert publisher is None


def test_create_market_data_publisher_creates_redis_publisher_when_enabled():
    FakeRedis.instances.clear()

    publisher = create_market_data_publisher(
        enabled=True,
        redis_url="redis://localhost:6379/0",
        redis_cls=FakeRedis,
        ttl_seconds=30,
    )

    assert publisher is not None
    assert FakeRedis.instances[0].url == "redis://localhost:6379/0"
    assert publisher.ttl_seconds == 30
