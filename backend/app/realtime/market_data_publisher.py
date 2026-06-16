import json
from typing import Protocol

from app.market_data.schemas import MarketBar
from app.realtime.cache_keys import MARKET_EVENTS_STREAM, latest_quote_key


class MarketDataPublisher(Protocol):
    def publish_bar(self, bar: MarketBar) -> None:
        pass


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
