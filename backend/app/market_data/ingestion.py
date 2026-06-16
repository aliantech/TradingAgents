from app.market_data.repository import MarketDataRepository
from app.market_data.schemas import MarketBar
from app.realtime.market_data_publisher import MarketDataPublisher


class MarketDataIngestionService:
    def __init__(self, repository: MarketDataRepository, *, publisher: MarketDataPublisher | None = None) -> None:
        self.repository = repository
        self.publisher = publisher

    def ingest_bars(
        self,
        bars: list[MarketBar],
        *,
        asset_type: str = "etf",
        exchange: str = "US",
    ) -> int:
        normalized_bars = [bar.model_copy(update={"symbol": bar.symbol.upper()}) for bar in bars]
        rows_written = self.repository.save_bars(normalized_bars, asset_type=asset_type, exchange=exchange)
        if self.publisher is not None:
            for bar in normalized_bars:
                self.publisher.publish_bar(bar)
        return rows_written
