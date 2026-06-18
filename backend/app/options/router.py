from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.market_data.repository import MarketDataRepository
from app.market_data.sync_repository import ProviderSyncRepository
from app.options.polygon_provider import OptionChainProvider, PolygonOptionsProvider
from app.options.repository import OptionContractRecord, OptionRepository, OptionSnapshotRecord
from app.options.schemas import (
    OptionBar,
    OptionBarsResponse,
    OptionChainResponse,
    OptionChainSyncRequest,
    OptionChainSyncResponse,
    OptionContract,
    OptionContractsResponse,
    OptionSnapshot,
)
from app.options.sync import OptionChainSyncService
from app.settings.runtime import resolve_runtime_settings

router = APIRouter(prefix="/api/options", tags=["options"])


def create_options_provider(provider_name: str, session: Session) -> OptionChainProvider:
    normalized_provider = provider_name.lower()
    if normalized_provider != "polygon":
        raise ValueError(f"Unsupported options provider: {provider_name}.")
    runtime_settings = resolve_runtime_settings(session)
    return PolygonOptionsProvider(
        api_key=runtime_settings.polygon_api_key,
        base_url=runtime_settings.polygon_base_url,
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
    return OptionChainResponse(
        underlying_symbol=normalized_underlying,
        expiry=expiry,
        snapshots=[_snapshot_to_schema(snapshot) for snapshot in snapshots],
    )


@router.get("/contracts", response_model=OptionContractsResponse)
def get_option_contracts(
    underlying: str = Query(default="SPX", min_length=1, max_length=32),
    expiry: str | None = Query(default=None, min_length=10, max_length=10),
    session: Session = Depends(get_db_session),
) -> OptionContractsResponse:
    normalized_underlying = underlying.upper()
    expiry_date = date.fromisoformat(expiry) if expiry else None
    repository = OptionRepository(session)
    contracts = repository.list_contracts(
        underlying_symbol=normalized_underlying,
        expiry=expiry_date,
    )
    return OptionContractsResponse(
        underlying_symbol=normalized_underlying,
        expiry=expiry,
        contracts=[_contract_to_schema(contract) for contract in contracts],
    )


@router.get("/bars", response_model=OptionBarsResponse)
def get_option_bars(
    option_symbol: str = Query(min_length=1, max_length=128),
    timeframe: str = Query(default="1m", pattern="^(1m|5m|1d)$"),
    session: Session = Depends(get_db_session),
) -> OptionBarsResponse:
    normalized_symbol = option_symbol.upper()
    bars = MarketDataRepository(session).list_bars(symbol=normalized_symbol, timeframe=timeframe)
    return OptionBarsResponse(
        option_symbol=normalized_symbol,
        timeframe=timeframe,
        bars=[
            OptionBar(
                option_symbol=bar.symbol,
                timeframe=bar.timeframe,
                timestamp=bar.timestamp,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
                source=bar.source,
            )
            for bar in bars
        ],
    )


@router.post("/sync-chain", response_model=OptionChainSyncResponse, status_code=202)
def sync_option_chain(
    request: OptionChainSyncRequest,
    session: Session = Depends(get_db_session),
) -> OptionChainSyncResponse:
    runtime_settings = resolve_runtime_settings(session)
    if not runtime_settings.manual_market_sync_enabled:
        raise HTTPException(status_code=403, detail="Manual options sync is disabled.")
    provider_name = request.provider.lower()
    try:
        provider = create_options_provider(provider_name, session)
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


def _contract_to_schema(contract: OptionContractRecord) -> OptionContract:
    return OptionContract(
        option_symbol=contract.option_symbol,
        underlying_symbol=contract.underlying_symbol,
        expiry=contract.expiry.isoformat(),
        strike=contract.strike,
        option_type=contract.option_type,
        exercise_style=contract.exercise_style,
        expiration_type=contract.expiration_type,
        source=contract.source,
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
