from app.market_data.repository import MarketDataRepository
from app.market_data.schemas import MarketBar


class MarketDataIngestionService:
    def __init__(self, repository: MarketDataRepository) -> None:
        self.repository = repository

    def ingest_bars(
        self,
        bars: list[MarketBar],
        *,
        asset_type: str = "etf",
        exchange: str = "US",
    ) -> int:
        normalized_bars = [bar.model_copy(update={"symbol": bar.symbol.upper()}) for bar in bars]
        return self.repository.save_bars(normalized_bars, asset_type=asset_type, exchange=exchange)
