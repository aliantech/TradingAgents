from dataclasses import dataclass
from datetime import UTC, date, datetime

from app.market_data.ingestion import MarketDataIngestionService
from app.market_data.provider import MarketDataProvider
from app.market_data.sync_repository import ProviderSyncRepository


@dataclass(frozen=True)
class MarketDataSyncResult:
    status: str
    rows_written: int
    error_message: str | None = None


class MarketDataSyncService:
    def __init__(
        self,
        *,
        provider: MarketDataProvider,
        provider_name: str,
        ingestion: MarketDataIngestionService,
        sync_repository: ProviderSyncRepository,
    ) -> None:
        self.provider = provider
        self.provider_name = provider_name
        self.ingestion = ingestion
        self.sync_repository = sync_repository

    def sync_daily_bars(self, symbol: str, start: date, end: date) -> MarketDataSyncResult:
        return self.sync_bars(symbol, "1d", start, end)

    def sync_bars(self, symbol: str, timeframe: str, start: date, end: date) -> MarketDataSyncResult:
        started_at = datetime.now(UTC)
        sync_type = "daily_bars" if timeframe == "1d" else f"bars_{timeframe}"
        try:
            bars = self.provider.fetch_bars(symbol.upper(), timeframe, start, end)
            rows_written = self.ingestion.ingest_bars(bars)
            self.sync_repository.record_run(
                provider=self.provider_name,
                sync_type=sync_type,
                status="succeeded",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                rows_written=rows_written,
            )
            return MarketDataSyncResult(status="succeeded", rows_written=rows_written)
        except Exception as exc:
            error_message = str(exc)
            self.sync_repository.record_run(
                provider=self.provider_name,
                sync_type=sync_type,
                status="failed",
                started_at=started_at,
                finished_at=datetime.now(UTC),
                rows_written=0,
                error_message=error_message,
            )
            return MarketDataSyncResult(status="failed", rows_written=0, error_message=error_message)
