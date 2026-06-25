from app.market_data.repository import MarketDataRepository
from app.market_data.schemas import MarketBar


def ingest_bars(
    repository: MarketDataRepository,
    bars: list[MarketBar],
    *,
    publisher=None,
    asset_type: str = "etf",
    exchange: str = "US",
) -> int:
    normalized_bars = [bar.model_copy(update={"symbol": bar.symbol.upper()}) for bar in bars]
    rows_written = repository.save_bars(normalized_bars, asset_type=asset_type, exchange=exchange)
    if publisher is not None:
        for bar in normalized_bars:
            publisher.publish_bar(bar)
    return rows_written
