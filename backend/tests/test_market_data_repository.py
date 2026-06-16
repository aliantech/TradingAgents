from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.market_data.repository import MarketDataRepository
from app.market_data.schemas import MarketBar


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_market_data_repository_upserts_and_reads_bars():
    session = _session()
    repository = MarketDataRepository(session)
    timestamp = datetime(2026, 6, 17, 13, 30, tzinfo=timezone.utc)

    first_bar = MarketBar(
        symbol="spy",
        timeframe="1m",
        timestamp=timestamp,
        open=550.0,
        high=551.0,
        low=549.5,
        close=550.5,
        volume=1_000_000,
        source="unit-test",
    )
    updated_bar = first_bar.model_copy(update={"close": 551.25, "volume": 1_200_000})

    repository.save_bars([first_bar])
    repository.save_bars([updated_bar])

    bars = repository.list_bars(symbol="SPY", timeframe="1m")

    assert len(bars) == 1
    assert bars[0].symbol == "SPY"
    assert bars[0].timestamp == timestamp
    assert bars[0].close == 551.25
    assert bars[0].volume == 1_200_000
