from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.market_data import scheduler
from app.market_data.scheduler import (
    ScheduledDailyBarSync,
    run_daily_bar_sync_schedule,
)
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


def test_parse_scheduler_targets_from_config_string():
    targets = scheduler.parse_scheduler_targets("SPY:1d:2, QQQ:5m:1")

    assert [target.symbol for target in targets] == ["SPY", "QQQ"]
    assert [target.timeframe for target in targets] == ["1d", "5m"]
    assert [target.lookback_days for target in targets] == [2, 1]


def test_parse_scheduler_targets_rejects_empty_config():
    with pytest.raises(ValueError, match="At least one scheduler target is required."):
        scheduler.parse_scheduler_targets(" ")


def test_run_configured_sync_targets_once_records_each_target():
    session = _session()
    today = date(2026, 6, 17)

    results = scheduler.run_configured_sync_targets_once(
        session=session,
        provider_name="sample",
        target_config="SPY:1d:2,QQQ:5m:1",
        today=today,
    )

    runs = ProviderSyncRepository(session).list_runs()
    assert [(result.symbol, result.timeframe, result.status) for result in results] == [
        ("SPY", "1d", "succeeded"),
        ("QQQ", "5m", "succeeded"),
    ]
    assert [result.rows_written for result in results] == [2, 1]
    assert len(runs) == 2
    assert {run.sync_type for run in runs} == {"daily_bars", "bars_5m"}
