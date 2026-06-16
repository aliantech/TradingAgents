from typing import Any

from app.realtime.market_data_publisher import MarketDataPublisher, RedisMarketDataPublisher


def create_market_data_publisher(
    *,
    enabled: bool,
    redis_url: str,
    ttl_seconds: int = 300,
    redis_cls: Any | None = None,
) -> MarketDataPublisher | None:
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
