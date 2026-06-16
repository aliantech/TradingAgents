from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.market_data.cli import run_sync_daily_bars
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
