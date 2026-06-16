from dataclasses import dataclass
from datetime import date, timedelta
from time import sleep
from typing import Callable

from sqlalchemy.orm import Session

from app.market_data.sync import MarketDataSyncResult


@dataclass(frozen=True)
class ScheduledDailyBarSync:
    symbols: list[str]
    start: date
    end: date


@dataclass(frozen=True)
class SchedulerTarget:
    symbol: str
    timeframe: str
    lookback_days: int


@dataclass(frozen=True)
class ScheduledSyncResult:
    symbol: str
    timeframe: str
    status: str
    rows_written: int
    error_message: str | None


@dataclass(frozen=True)
class SchedulerLoopIteration:
    iteration: int
    results: list[ScheduledSyncResult]


def run_daily_bar_sync_schedule(
    *,
    session: Session,
    provider_name: str,
    schedule: ScheduledDailyBarSync,
) -> list[MarketDataSyncResult]:
    from app.market_data.cli import run_sync_daily_bars

    return [
        run_sync_daily_bars(
            session=session,
            provider_name=provider_name,
            symbol=symbol,
            start=schedule.start,
            end=schedule.end,
        )
        for symbol in schedule.symbols
    ]


def parse_scheduler_targets(value: str) -> list[SchedulerTarget]:
    targets: list[SchedulerTarget] = []
    for raw_item in value.split(","):
        item = raw_item.strip()
        if not item:
            continue
        parts = [part.strip() for part in item.split(":")]
        if len(parts) != 3:
            raise ValueError("Scheduler target must use SYMBOL:timeframe:lookback_days format.")
        symbol, timeframe, raw_lookback_days = parts
        if timeframe not in {"1m", "5m", "1d"}:
            raise ValueError(f"Unsupported scheduler timeframe: {timeframe}")
        lookback_days = int(raw_lookback_days)
        if lookback_days < 0:
            raise ValueError("Scheduler lookback_days must be zero or greater.")
        targets.append(SchedulerTarget(symbol=symbol.upper(), timeframe=timeframe, lookback_days=lookback_days))
    if not targets:
        raise ValueError("At least one scheduler target is required.")
    return targets


def run_configured_sync_targets_once(
    *,
    session: Session,
    provider_name: str,
    target_config: str,
    today: date,
) -> list[ScheduledSyncResult]:
    from app.market_data.cli import run_sync_bars

    results: list[ScheduledSyncResult] = []
    for target in parse_scheduler_targets(target_config):
        result = run_sync_bars(
            session=session,
            provider_name=provider_name,
            symbol=target.symbol,
            timeframe=target.timeframe,
            start=today - timedelta(days=max(target.lookback_days - 1, 0)),
            end=today,
        )
        results.append(
            ScheduledSyncResult(
                symbol=target.symbol,
                timeframe=target.timeframe,
                status=result.status,
                rows_written=result.rows_written,
                error_message=result.error_message,
            )
        )
    return results


def run_scheduler_loop(
    *,
    session_factory: Callable[[], Session],
    provider_name: str,
    target_config: str,
    interval_seconds: int,
    today_fn: Callable[[], date] = date.today,
    sleep_fn: Callable[[int], None] = sleep,
    max_iterations: int | None = None,
) -> list[SchedulerLoopIteration]:
    if interval_seconds < 1:
        raise ValueError("Scheduler interval_seconds must be at least 1.")
    if max_iterations is not None and max_iterations < 1:
        raise ValueError("Scheduler max_iterations must be at least 1 when provided.")

    iterations: list[SchedulerLoopIteration] = []
    iteration = 0
    while max_iterations is None or iteration < max_iterations:
        iteration += 1
        session = session_factory()
        try:
            results = run_configured_sync_targets_once(
                session=session,
                provider_name=provider_name,
                target_config=target_config,
                today=today_fn(),
            )
        finally:
            session.close()
        if max_iterations is not None:
            iterations.append(SchedulerLoopIteration(iteration=iteration, results=results))
        if max_iterations is None or iteration < max_iterations:
            sleep_fn(interval_seconds)
    return iterations
