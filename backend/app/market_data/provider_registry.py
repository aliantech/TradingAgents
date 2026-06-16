from app.market_data.provider import MarketDataProvider
from app.market_data.polygon_provider import PolygonMarketDataProvider
from app.market_data.sample_provider import SampleMarketDataProvider


def get_market_data_provider(
    name: str,
    *,
    polygon_api_key: str = "",
    polygon_base_url: str = "https://api.polygon.io",
    max_retries: int = 2,
    retry_backoff_seconds: float = 1.0,
) -> MarketDataProvider:
    normalized_name = name.lower().strip()
    if normalized_name == "sample":
        return SampleMarketDataProvider()
    if normalized_name == "polygon":
        return PolygonMarketDataProvider(
            api_key=polygon_api_key,
            base_url=polygon_base_url,
            max_retries=max_retries,
            retry_backoff_seconds=retry_backoff_seconds,
        )
    supported = "sample, polygon"
    raise ValueError(f"Unsupported market data provider: {name}. Supported providers: {supported}.")
