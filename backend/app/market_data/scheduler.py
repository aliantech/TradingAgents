from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.market_data.cli import run_sync_daily_bars
from app.market_data.sync import MarketDataSyncResult


@dataclass(frozen=True)
class ScheduledDailyBarSync:
    symbols: list[str]
    start: date
    end: date


def run_daily_bar_sync_schedule(
    *,
    session: Session,
    provider_name: str,
    schedule: ScheduledDailyBarSync,
) -> list[MarketDataSyncResult]:
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
