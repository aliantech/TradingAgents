from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db_session
from app.market_data.sync_repository import ProviderSyncRepository
from app.options.polygon_provider import OptionChainProvider, PolygonOptionsProvider
from app.options.repository import OptionRepository, OptionSnapshotRecord
from app.options.sample_data import seed_sample_option_chain
from app.options.schemas import OptionChainResponse, OptionChainSyncRequest, OptionChainSyncResponse, OptionSnapshot
from app.options.sync import OptionChainSyncService

router = APIRouter(prefix="/api/options", tags=["options"])


def create_options_provider(provider_name: str) -> OptionChainProvider:
    normalized_provider = provider_name.lower()
    if normalized_provider != "polygon":
        raise ValueError(f"Unsupported options provider: {provider_name}.")
    return PolygonOptionsProvider(
        api_key=settings.polygon_api_key,
        base_url=settings.polygon_base_url,
    )


@router.get("/chain", response_model=OptionChainResponse)
def get_option_chain(
    underlying: str = Query(default="SPX", min_length=1, max_length=32),
    expiry: str = Query(default="2026-06-17", min_length=10, max_length=10),
    session: Session = Depends(get_db_session),
) -> OptionChainResponse:
    normalized_underlying = underlying.upper()
    expiry_date = date.fromisoformat(expiry)
    repository = OptionRepository(session)
    snapshots = repository.list_chain_snapshots(
        underlying_symbol=normalized_underlying,
        expiry=expiry_date,
    )
    if not snapshots:
        seed_sample_option_chain(
            repository,
            underlying_symbol=normalized_underlying,
            expiry=expiry_date,
        )
        snapshots = repository.list_chain_snapshots(
            underlying_symbol=normalized_underlying,
            expiry=expiry_date,
        )
    return OptionChainResponse(
        underlying_symbol=normalized_underlying,
        expiry=expiry,
        snapshots=[_snapshot_to_schema(snapshot) for snapshot in snapshots],
    )


@router.post("/sync-chain", response_model=OptionChainSyncResponse, status_code=202)
def sync_option_chain(
    request: OptionChainSyncRequest,
    session: Session = Depends(get_db_session),
) -> OptionChainSyncResponse:
    if not settings.manual_market_sync_enabled:
        raise HTTPException(status_code=403, detail="Manual options sync is disabled.")
    provider_name = request.provider.lower()
    try:
        provider = create_options_provider(provider_name)
        result = OptionChainSyncService(
            provider=provider,
            provider_name=provider_name,
            option_repository=OptionRepository(session),
            sync_repository=ProviderSyncRepository(session),
        ).sync_chain(
            underlying_symbol=request.underlying_symbol,
            expiry=request.expiry,
            limit=request.limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OptionChainSyncResponse(
        provider=result.provider,
        underlying_symbol=result.underlying_symbol,
        expiry=result.expiry,
        status=result.status,
        rows_written=result.rows_written,
        error_message=result.error_message,
    )


def _snapshot_to_schema(snapshot: OptionSnapshotRecord) -> OptionSnapshot:
    return OptionSnapshot(
        option_symbol=snapshot.option_symbol,
        underlying_symbol=snapshot.underlying_symbol,
        timestamp=snapshot.timestamp,
        bid=snapshot.bid,
        ask=snapshot.ask,
        last=snapshot.last,
        volume=snapshot.volume,
        open_interest=snapshot.open_interest,
        implied_volatility=snapshot.implied_volatility,
        delta=snapshot.delta,
        gamma=snapshot.gamma,
        theta=snapshot.theta,
        vega=snapshot.vega,
        source=snapshot.source,
    )
