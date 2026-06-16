from collections.abc import Callable
from datetime import UTC, date, datetime
from time import sleep as default_sleep
from typing import Protocol
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

from app.market_data.provider import MarketDataProvider
from app.market_data.schemas import MarketBar
from app.market_data.symbols import map_provider_symbol


class ProviderRateLimitError(RuntimeError):
    pass


class ProviderTransportError(RuntimeError):
    pass


class JsonTransport(Protocol):
    def get_json(self, url: str) -> dict:
        pass


class UrlLibJsonTransport:
    def get_json(self, url: str) -> dict:
        import json

        try:
            with urlopen(url, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 429:
                raise ProviderRateLimitError("polygon rate limit exceeded") from exc
            if exc.code >= 500:
                raise ProviderTransportError(f"polygon server error: {exc.code}") from exc
            raise


class PolygonMarketDataProvider(MarketDataProvider):
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.polygon.io",
        transport: JsonTransport | None = None,
        max_retries: int = 2,
        retry_backoff_seconds: float = 1.0,
        sleep: Callable[[float], None] = default_sleep,
    ) -> None:
        if not api_key:
            raise ValueError("AQUANTLENS_POLYGON_API_KEY is required for polygon market data provider.")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.transport = transport or UrlLibJsonTransport()
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds
        self.sleep = sleep

    def fetch_daily_bars(self, symbol: str, start: date, end: date) -> list[MarketBar]:
        return self.fetch_bars(symbol, "1d", start, end)

    def fetch_bars(self, symbol: str, timeframe: str, start: date, end: date) -> list[MarketBar]:
        normalized_symbol = symbol.upper()
        provider_symbol = map_provider_symbol(normalized_symbol, "polygon")
        multiplier, timespan = _polygon_timeframe(timeframe)
        path = (
            f"/v2/aggs/ticker/{provider_symbol}/range/{multiplier}/{timespan}/"
            f"{start.isoformat()}/{end.isoformat()}"
        )
        query = urlencode({"adjusted": "true", "sort": "asc", "apiKey": self.api_key})
        payload = self._get_with_retry(f"{self.base_url}{path}?{query}")
        return [
            MarketBar(
                symbol=normalized_symbol,
                timeframe=timeframe,
                timestamp=_timestamp_from_ms(row["t"]),
                open=float(row["o"]),
                high=float(row["h"]),
                low=float(row["l"]),
                close=float(row["c"]),
                volume=int(row.get("v", 0)),
                source="polygon",
            )
            for row in payload.get("results", [])
        ]

    def _get_with_retry(self, url: str) -> dict:
        attempts = 0
        while True:
            try:
                return self.transport.get_json(url)
            except (ProviderRateLimitError, ProviderTransportError):
                if attempts >= self.max_retries:
                    raise
                attempts += 1
                self.sleep(self.retry_backoff_seconds * attempts)


def _timestamp_from_ms(value: int) -> datetime:
    return datetime.fromtimestamp(value / 1000, tz=UTC)


def _polygon_timeframe(timeframe: str) -> tuple[int, str]:
    if timeframe == "1d":
        return 1, "day"
    if timeframe == "1m":
        return 1, "minute"
    if timeframe == "5m":
        return 5, "minute"
    raise ValueError(f"Unsupported Polygon timeframe: {timeframe}. Supported: 1m, 5m, 1d.")
