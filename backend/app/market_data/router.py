from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.market_data.repository import MarketDataRepository
from app.market_data.schemas import MarketBar, MarketBarsResponse, ProviderSyncRunItem, ProviderSyncRunsResponse
from app.market_data.sync_repository import ProviderSyncRepository

router = APIRouter(prefix="/api/market-data", tags=["market-data"])


def _sample_bars(symbol: str, timeframe: str) -> list[MarketBar]:
    start = datetime(2026, 6, 17, 13, 30, tzinfo=timezone.utc)
    prices = [550.0, 551.2, 550.7, 552.1, 553.0, 552.4, 554.2, 555.0]
    bars: list[MarketBar] = []
    for index, price in enumerate(prices):
        open_price = prices[index - 1] if index else price - 0.5
        bars.append(
            MarketBar(
                symbol=symbol.upper(),
                timeframe=timeframe,
                timestamp=start + timedelta(minutes=index),
                open=open_price,
                high=max(open_price, price) + 0.4,
                low=min(open_price, price) - 0.3,
                close=price,
                volume=900000 + index * 75000,
                source="sample",
            )
        )
    return bars


@router.get("/bars", response_model=MarketBarsResponse)
def get_market_bars(
    symbol: str = Query(default="SPY", min_length=1, max_length=32),
    timeframe: str = Query(default="1m", pattern="^(1m|5m|1d)$"),
    session: Session = Depends(get_db_session),
) -> MarketBarsResponse:
    normalized_symbol = symbol.upper()
    repository = MarketDataRepository(session)
    persisted_bars = repository.list_bars(symbol=normalized_symbol, timeframe=timeframe)
    return MarketBarsResponse(
        symbol=normalized_symbol,
        timeframe=timeframe,
        bars=persisted_bars or _sample_bars(normalized_symbol, timeframe),
    )


@router.get("/sync-runs", response_model=ProviderSyncRunsResponse)
def list_sync_runs(
    limit: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_db_session),
) -> ProviderSyncRunsResponse:
    repository = ProviderSyncRepository(session)
    return ProviderSyncRunsResponse(
        runs=[
            ProviderSyncRunItem(
                id=str(run.id),
                provider=run.provider,
                sync_type=run.sync_type,
                status=run.status,
                started_at=run.started_at,
                finished_at=run.finished_at,
                rows_written=run.rows_written,
                error_message=run.error_message,
            )
            for run in repository.list_runs(limit=limit)
        ]
    )
