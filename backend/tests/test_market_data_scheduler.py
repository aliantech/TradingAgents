from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.market_data import scheduler
from app.market_data.sync import MarketDataSyncResult
from app.market_data.scheduler import (
    ScheduledDailyBarSync,
    run_daily_bar_sync_schedule,
)
from app.market_data.sync_repository import ProviderSyncRepository


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def fake_sync_daily_bars(*, session, provider_name, symbol, start, end):
    return MarketDataSyncResult(
        status="succeeded",
        rows_written=(end - start).days + 1,
        error_message=None,
    )


def fake_sync_bars(*, session, provider_name, symbol, timeframe, start, end):
    return MarketDataSyncResult(
        status="succeeded",
        rows_written=(end - start).days + 1,
        error_message=None,
    )


def test_daily_bar_sync_schedule_runs_each_symbol(monkeypatch):
    session = _session()
    from app.market_data import cli

    monkeypatch.setattr(cli, "run_sync_daily_bars", fake_sync_daily_bars)

    results = run_daily_bar_sync_schedule(
        session=session,
        provider_name="fixture",
        schedule=ScheduledDailyBarSync(
            symbols=["spy", "qqq"],
            start=date(2026, 6, 17),
            end=date(2026, 6, 17),
        ),
    )

    runs = ProviderSyncRepository(session).list_runs()
    assert [result.rows_written for result in results] == [1, 1]
    assert len(runs) == 0


def test_parse_scheduler_targets_from_config_string():
    targets = scheduler.parse_scheduler_targets("SPY:1d:2, QQQ:5m:1")

    assert [target.symbol for target in targets] == ["SPY", "QQQ"]
    assert [target.timeframe for target in targets] == ["1d", "5m"]
    assert [target.lookback_days for target in targets] == [2, 1]


def test_parse_scheduler_targets_rejects_empty_config():
    with pytest.raises(ValueError, match="At least one scheduler target is required."):
        scheduler.parse_scheduler_targets(" ")


def test_run_configured_sync_targets_once_records_each_target(monkeypatch):
    session = _session()
    today = date(2026, 6, 17)
    from app.market_data import cli

    monkeypatch.setattr(cli, "run_sync_bars", fake_sync_bars)

    results = scheduler.run_configured_sync_targets_once(
        session=session,
        provider_name="fixture",
        target_config="SPY:1d:2,QQQ:5m:1",
        today=today,
    )

    runs = ProviderSyncRepository(session).list_runs()
    assert [(result.symbol, result.timeframe, result.status) for result in results] == [
        ("SPY", "1d", "succeeded"),
        ("QQQ", "5m", "succeeded"),
    ]
    assert [result.rows_written for result in results] == [2, 1]
    assert len(runs) == 0


def test_run_scheduler_loop_runs_configured_targets_for_limited_iterations(monkeypatch):
    session = _session()
    sleeps = []
    from app.market_data import cli

    monkeypatch.setattr(cli, "run_sync_bars", fake_sync_bars)

    iterations = scheduler.run_scheduler_loop(
        session_factory=lambda: session,
        provider_name="fixture",
        target_config="SPY:1d:2",
        today_fn=lambda: date(2026, 6, 17),
        interval_seconds=15,
        max_iterations=2,
        sleep_fn=sleeps.append,
    )

    runs = ProviderSyncRepository(session).list_runs()
    assert [iteration.iteration for iteration in iterations] == [1, 2]
    assert [iteration.results[0].rows_written for iteration in iterations] == [2, 2]
    assert sleeps == [15]
    assert len(runs) == 0
