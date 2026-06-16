from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.market_data.ingestion import MarketDataIngestionService
from app.market_data.repository import MarketDataRepository
from app.market_data.schemas import MarketBar


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_market_data_ingestion_service_writes_normalized_bars():
    session = _session()
    repository = MarketDataRepository(session)
    service = MarketDataIngestionService(repository)

    rows_written = service.ingest_bars(
        [
            MarketBar(
                symbol="spy",
                timeframe="1m",
                timestamp=datetime(2026, 6, 17, 13, 30, tzinfo=timezone.utc),
                open=550.0,
                high=551.0,
                low=549.5,
                close=550.5,
                volume=1_000_000,
                source="unit-test",
            )
        ]
    )

    bars = repository.list_bars(symbol="SPY", timeframe="1m")

    assert rows_written == 1
    assert len(bars) == 1
    assert bars[0].symbol == "SPY"
    assert bars[0].source == "unit-test"
