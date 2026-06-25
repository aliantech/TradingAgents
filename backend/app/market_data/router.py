from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db_session
from app.market_data.finance_data_hub import FinanceDataHubClient, FinanceDataHubError
from app.market_data.repository import MarketDataRepository
from app.market_data.schemas import (
    MarketBar,
    MarketBarsResponse,
    ProviderReadinessResponse,
    ProviderSyncRunItem,
    ProviderSyncRunsResponse,
    ProviderSyncHealthResponse,
    ProviderSyncSummaryGroupItem,
    ProviderSyncSummaryGroupsResponse,
    ProviderSyncSummaryResponse,
)
from app.market_data.provider_readiness import check_market_data_provider_readiness
from app.market_data.sync_repository import ProviderSyncRepository
from app.settings.runtime import resolve_runtime_settings

router = APIRouter(prefix="/api/market-data", tags=["market-data"])


@router.get("/bars", response_model=MarketBarsResponse)
def get_market_bars(
    symbol: str = Query(default="SPY", min_length=1, max_length=32),
    timeframe: str = Query(default="1m", pattern="^(1m|5m|1d)$"),
    session: Session = Depends(get_db_session),
) -> MarketBarsResponse:
    normalized_symbol = symbol.upper()
    runtime_settings = resolve_runtime_settings(session)
    try:
        hub_bars = FinanceDataHubClient(runtime_settings.finance_data_hub_base_url).list_bars(
            symbol=normalized_symbol,
            timeframe=timeframe,
        )
        if hub_bars:
            return MarketBarsResponse(symbol=normalized_symbol, timeframe=timeframe, bars=hub_bars)
    except FinanceDataHubError:
        pass
    repository = MarketDataRepository(session)
    persisted_bars = repository.list_bars(symbol=normalized_symbol, timeframe=timeframe)
    return MarketBarsResponse(
        symbol=normalized_symbol,
        timeframe=timeframe,
        bars=persisted_bars,
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
                target_symbol=run.target_symbol,
                target_expiry=run.target_expiry,
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


@router.get("/sync-health", response_model=ProviderSyncHealthResponse)
def get_sync_health(
    provider: str | None = Query(default=None, min_length=1, max_length=64),
    sync_type: str = Query(default="daily_bars", min_length=1, max_length=64),
    now: datetime | None = Query(default=None),
    stale_after_minutes: int = Query(default=settings.provider_sync_stale_after_minutes, ge=1, le=10080),
    failure_rate_threshold: float = Query(default=settings.provider_sync_failure_rate_threshold, ge=0.0, le=1.0),
    session: Session = Depends(get_db_session),
) -> ProviderSyncHealthResponse:
    health = ProviderSyncRepository(session).evaluate_health(
        provider=provider or settings.market_data_provider,
        sync_type=sync_type,
        now=now or datetime.now(timezone.utc),
        stale_after_minutes=stale_after_minutes,
        failure_rate_threshold=failure_rate_threshold,
    )
    return ProviderSyncHealthResponse(
        provider=health.provider,
        sync_type=health.sync_type,
        status=health.status,
        total_runs=health.total_runs,
        failed_runs=health.failed_runs,
        failure_rate=health.failure_rate,
        latest_status=health.latest_status,
        latest_finished_at=health.latest_finished_at,
        minutes_since_latest=health.minutes_since_latest,
        stale_after_minutes=health.stale_after_minutes,
        message=health.message,
    )


@router.get("/provider-readiness", response_model=ProviderReadinessResponse)
def get_provider_readiness(
    provider: str | None = Query(default=None, min_length=1, max_length=64),
    session: Session = Depends(get_db_session),
) -> ProviderReadinessResponse:
    runtime_settings = resolve_runtime_settings(session)
    readiness = check_market_data_provider_readiness(runtime_settings, provider=provider)
    return ProviderReadinessResponse(
        provider=readiness.provider,
        ready=readiness.ready,
        missing=readiness.missing,
        message=readiness.message,
    )
