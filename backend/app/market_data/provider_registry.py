from app.market_data.provider import MarketDataProvider
from app.market_data.sample_provider import SampleMarketDataProvider


def get_market_data_provider(name: str) -> MarketDataProvider:
    normalized_name = name.lower().strip()
    if normalized_name == "sample":
        return SampleMarketDataProvider()
    supported = "sample"
    raise ValueError(f"Unsupported market data provider: {name}. Supported providers: {supported}.")
