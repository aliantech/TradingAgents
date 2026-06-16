from datetime import date, datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.market_data.ingestion import MarketDataIngestionService
from app.market_data.provider import MarketDataProvider
from app.market_data.repository import MarketDataRepository
from app.market_data.schemas import MarketBar
from app.market_data.sync import MarketDataSyncService
from app.market_data.sync_repository import ProviderSyncRepository


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


class FakeProvider(MarketDataProvider):
    def fetch_bars(self, symbol: str, timeframe: str, start: date, end: date) -> list[MarketBar]:
        return [
            MarketBar(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=datetime(2026, 6, 17, 13, 30, tzinfo=timezone.utc),
                open=550.0,
                high=553.0,
                low=549.5,
                close=552.2,
                volume=90_000_000,
                source="fake",
            )
        ]

    def fetch_daily_bars(self, symbol: str, start: date, end: date) -> list[MarketBar]:
        return self.fetch_bars(symbol, "1d", start, end)


class FailingProvider(MarketDataProvider):
    def fetch_bars(self, symbol: str, timeframe: str, start: date, end: date) -> list[MarketBar]:
        raise RuntimeError("provider timeout")

    def fetch_daily_bars(self, symbol: str, start: date, end: date) -> list[MarketBar]:
        raise RuntimeError("provider timeout")


def test_market_data_sync_records_successful_daily_bar_run():
    session = _session()
    bar_repository = MarketDataRepository(session)
    sync_repository = ProviderSyncRepository(session)
    service = MarketDataSyncService(
        provider=FakeProvider(),
        provider_name="fake",
        ingestion=MarketDataIngestionService(bar_repository),
        sync_repository=sync_repository,
    )

    result = service.sync_daily_bars("spy", date(2026, 6, 17), date(2026, 6, 17))

    bars = bar_repository.list_bars(symbol="SPY", timeframe="1d")
    runs = sync_repository.list_runs()
    assert result.status == "succeeded"
    assert result.rows_written == 1
    assert len(bars) == 1
    assert bars[0].symbol == "SPY"
    assert len(runs) == 1
    assert runs[0].provider == "fake"
    assert runs[0].sync_type == "daily_bars"
    assert runs[0].status == "succeeded"
    assert runs[0].rows_written == 1


def test_market_data_sync_records_failed_provider_run():
    session = _session()
    sync_repository = ProviderSyncRepository(session)
    service = MarketDataSyncService(
        provider=FailingProvider(),
        provider_name="fake",
        ingestion=MarketDataIngestionService(MarketDataRepository(session)),
        sync_repository=sync_repository,
    )

    result = service.sync_daily_bars("SPY", date(2026, 6, 17), date(2026, 6, 17))

    runs = sync_repository.list_runs()
    assert result.status == "failed"
    assert result.rows_written == 0
    assert "provider timeout" in (result.error_message or "")
    assert len(runs) == 1
    assert runs[0].status == "failed"
    assert runs[0].rows_written == 0
    assert "provider timeout" in (runs[0].error_message or "")


def test_market_data_sync_supports_intraday_timeframes():
    session = _session()
    bar_repository = MarketDataRepository(session)
    sync_repository = ProviderSyncRepository(session)
    service = MarketDataSyncService(
        provider=FakeProvider(),
        provider_name="fake",
        ingestion=MarketDataIngestionService(bar_repository),
        sync_repository=sync_repository,
    )

    result = service.sync_bars("spy", "1m", date(2026, 6, 17), date(2026, 6, 17))

    bars = bar_repository.list_bars(symbol="SPY", timeframe="1m")
    runs = sync_repository.list_runs()
    assert result.status == "succeeded"
    assert result.rows_written == 1
    assert len(bars) == 1
    assert runs[0].sync_type == "bars_1m"
