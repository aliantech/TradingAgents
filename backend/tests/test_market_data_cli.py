from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.market_data.cli import run_sync_bars, run_sync_daily_bars
from app.market_data.repository import MarketDataRepository
from app.market_data.sync_repository import ProviderSyncRepository


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_run_sync_daily_bars_uses_configured_provider_and_records_audit():
    session = _session()

    result = run_sync_daily_bars(
        session=session,
        provider_name="sample",
        symbol="spy",
        start=date(2026, 6, 16),
        end=date(2026, 6, 17),
    )

    bars = MarketDataRepository(session).list_bars(symbol="SPY", timeframe="1d")
    runs = ProviderSyncRepository(session).list_runs()
    assert result.status == "succeeded"
    assert result.rows_written == 2
    assert len(bars) == 2
    assert bars[0].symbol == "SPY"
    assert bars[0].source == "sample"
    assert len(runs) == 1
    assert runs[0].provider == "sample"
    assert runs[0].status == "succeeded"


def test_run_sync_daily_bars_publishes_when_realtime_enabled(monkeypatch):
    session = _session()
    published = []

    class FakePublisher:
        def publish_bar(self, bar):
            published.append(bar)

    monkeypatch.setattr("app.market_data.cli.create_market_data_publisher", lambda **kwargs: FakePublisher())
    monkeypatch.setattr("app.market_data.cli.settings.realtime_market_publish_enabled", True)

    result = run_sync_daily_bars(
        session=session,
        provider_name="sample",
        symbol="SPY",
        start=date(2026, 6, 17),
        end=date(2026, 6, 17),
    )

    assert result.status == "succeeded"
    assert len(published) == 1
    assert published[0].symbol == "SPY"


def test_run_sync_bars_supports_intraday_timeframe():
    session = _session()

    result = run_sync_bars(
        session=session,
        provider_name="sample",
        symbol="SPY",
        timeframe="5m",
        start=date(2026, 6, 17),
        end=date(2026, 6, 17),
    )

    bars = MarketDataRepository(session).list_bars(symbol="SPY", timeframe="5m")
    assert result.status == "succeeded"
    assert result.rows_written == 1
    assert len(bars) == 1
