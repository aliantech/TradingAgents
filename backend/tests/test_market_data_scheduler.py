from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.market_data.scheduler import ScheduledDailyBarSync, run_daily_bar_sync_schedule
from app.market_data.sync_repository import ProviderSyncRepository


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_daily_bar_sync_schedule_runs_each_symbol():
    session = _session()

    results = run_daily_bar_sync_schedule(
        session=session,
        provider_name="sample",
        schedule=ScheduledDailyBarSync(
            symbols=["spy", "qqq"],
            start=date(2026, 6, 17),
            end=date(2026, 6, 17),
        ),
    )

    runs = ProviderSyncRepository(session).list_runs()
    assert [result.rows_written for result in results] == [1, 1]
    assert len(runs) == 2
    assert all(run.status == "succeeded" for run in runs)
