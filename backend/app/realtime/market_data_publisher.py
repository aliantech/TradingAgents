import json
from typing import Any

from app.market_data.schemas import MarketBar
from app.realtime.cache_keys import MARKET_EVENTS_STREAM, latest_quote_key


class RedisMarketDataPublisher:
    def __init__(self, client, *, ttl_seconds: int = 300) -> None:
        self.client = client
        self.ttl_seconds = ttl_seconds

    def publish_bar(self, bar: MarketBar) -> None:
        normalized_bar = bar.model_copy(update={"symbol": bar.symbol.upper()})
        payload = json.dumps(normalized_bar.model_dump(mode="json"), ensure_ascii=False)
        self.client.set(latest_quote_key(normalized_bar.symbol), payload, ex=self.ttl_seconds)
        self.client.xadd(
            MARKET_EVENTS_STREAM,
            {
                "event_type": "bar",
                "symbol": normalized_bar.symbol,
                "timeframe": normalized_bar.timeframe,
                "payload": payload,
            },
        )


def create_market_data_publisher(
    *,
    enabled: bool,
    redis_url: str,
    ttl_seconds: int = 300,
    redis_cls: Any | None = None,
):
    if not enabled:
        return None
    redis_client_cls = redis_cls or _load_redis_client()
    client = redis_client_cls.from_url(redis_url)
    return RedisMarketDataPublisher(client, ttl_seconds=ttl_seconds)


def _load_redis_client():
    try:
        from redis import Redis
    except ImportError as exc:
        raise RuntimeError("Install redis to enable realtime market publishing.") from exc
    return Redis
