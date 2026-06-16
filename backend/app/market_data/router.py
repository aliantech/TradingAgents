from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db_session
from app.market_data.cli import run_sync_bars
from app.market_data.repository import MarketDataRepository
from app.market_data.schemas import (
    DailyBarSyncRequest,
    DailyBarSyncResponse,
    MarketBar,
    MarketBarsResponse,
    ProviderSyncRunItem,
    ProviderSyncRunsResponse,
    ProviderSyncSummaryGroupItem,
    ProviderSyncSummaryGroupsResponse,
    ProviderSyncSummaryResponse,
)
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
    provider: str | None = Query(default=None, min_length=1, max_length=64),
    sync_type: str | None = Query(default=None, min_length=1, max_length=64),
    started_after: datetime | None = Query(default=None),
    started_before: datetime | None = Query(default=None),
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
            for run in repository.list_runs(
                limit=limit,
                provider=provider,
                sync_type=sync_type,
                started_after=started_after,
                started_before=started_before,
            )
        ]
    )


@router.get("/sync-summary", response_model=ProviderSyncSummaryResponse)
def get_sync_summary(
    provider: str | None = Query(default=None, min_length=1, max_length=64),
    sync_type: str | None = Query(default=None, min_length=1, max_length=64),
    started_after: datetime | None = Query(default=None),
    started_before: datetime | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> ProviderSyncSummaryResponse:
    summary = ProviderSyncRepository(session).summarize_runs(
        provider=provider,
        sync_type=sync_type,
        started_after=started_after,
        started_before=started_before,
    )
    return ProviderSyncSummaryResponse(
        total_runs=summary.total_runs,
        succeeded=summary.succeeded,
        failed=summary.failed,
        rows_written=summary.rows_written,
        latest_status=summary.latest_status,
        latest_finished_at=summary.latest_finished_at,
        average_duration_ms=summary.average_duration_ms,
    )


@router.get("/sync-summary/groups", response_model=ProviderSyncSummaryGroupsResponse)
def get_sync_summary_groups(
    provider: str | None = Query(default=None, min_length=1, max_length=64),
    sync_type: str | None = Query(default=None, min_length=1, max_length=64),
    started_after: datetime | None = Query(default=None),
    started_before: datetime | None = Query(default=None),
    session: Session = Depends(get_db_session),
) -> ProviderSyncSummaryGroupsResponse:
    groups = ProviderSyncRepository(session).summarize_groups(
        provider=provider,
        sync_type=sync_type,
        started_after=started_after,
        started_before=started_before,
    )
    return ProviderSyncSummaryGroupsResponse(
        groups=[
            ProviderSyncSummaryGroupItem(
                provider=group.provider,
                sync_type=group.sync_type,
                total_runs=group.total_runs,
                succeeded=group.succeeded,
                failed=group.failed,
                rows_written=group.rows_written,
                latest_status=group.latest_status,
                latest_finished_at=group.latest_finished_at,
                average_duration_ms=group.average_duration_ms,
            )
            for group in groups
        ]
    )


@router.post("/sync-daily-bars", response_model=DailyBarSyncResponse, status_code=202)
def sync_daily_bars(
    request: DailyBarSyncRequest,
    session: Session = Depends(get_db_session),
) -> DailyBarSyncResponse:
    if not settings.manual_market_sync_enabled:
        raise HTTPException(status_code=403, detail="Manual market data sync is disabled.")
    try:
        result = run_sync_bars(
            session=session,
            provider_name=request.provider or settings.market_data_provider,
            symbol=request.symbol,
            timeframe=request.timeframe,
            start=request.start,
            end=request.end,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return DailyBarSyncResponse(
        status=result.status,
        rows_written=result.rows_written,
        error_message=result.error_message,
    )
