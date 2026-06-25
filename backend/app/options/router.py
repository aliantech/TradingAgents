from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.market_data.finance_data_hub import FinanceDataHubClient, FinanceDataHubError
from app.market_data.repository import MarketDataRepository
from app.options.repository import OptionContractRecord, OptionRepository, OptionSnapshotRecord
from app.options.schemas import (
    OptionBar,
    OptionBarsResponse,
    OptionChainResponse,
    OptionContract,
    OptionContractsResponse,
    OptionQuoteHistoryResponse,
    OptionSnapshot,
)
from app.settings.runtime import resolve_runtime_settings

router = APIRouter(prefix="/api/options", tags=["options"])


@router.get("/chain", response_model=OptionChainResponse)
def get_option_chain(
    underlying: str = Query(default="SPX", min_length=1, max_length=32),
    expiry: str | None = Query(default=None, min_length=10, max_length=10),
    session: Session = Depends(get_db_session),
) -> OptionChainResponse:
    normalized_underlying = underlying.upper()
    expiry_date = date.fromisoformat(expiry) if expiry else None
    runtime_settings = resolve_runtime_settings(session)
    try:
        if expiry_date is None:
            expiry_date = _nearest_hub_expiry(
                FinanceDataHubClient(runtime_settings.finance_data_hub_base_url).list_option_latest_quote_rows(
                    underlying_symbol=normalized_underlying,
                )
            )
        if expiry_date is not None:
            hub_snapshots = FinanceDataHubClient(runtime_settings.finance_data_hub_base_url).list_option_latest_quotes(
                underlying_symbol=normalized_underlying,
                expiry=expiry_date,
            )
            if hub_snapshots:
                return OptionChainResponse(
                    underlying_symbol=normalized_underlying,
                    expiry=expiry_date.isoformat(),
                    snapshots=[_snapshot_to_schema(snapshot) for snapshot in hub_snapshots],
                )
    except FinanceDataHubError:
        pass
    if expiry_date is None:
        expiry_date = next_friday()
    repository = OptionRepository(session)
    snapshots = repository.list_chain_snapshots(
        underlying_symbol=normalized_underlying,
        expiry=expiry_date,
    )
    return OptionChainResponse(
        underlying_symbol=normalized_underlying,
        expiry=expiry_date.isoformat(),
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
    runtime_settings = resolve_runtime_settings(session)
    try:
        hub_contracts = FinanceDataHubClient(runtime_settings.finance_data_hub_base_url).list_option_contracts(
            underlying_symbol=normalized_underlying,
            expiry=expiry_date,
        )
        if hub_contracts:
            return OptionContractsResponse(
                underlying_symbol=normalized_underlying,
                expiry=expiry,
                contracts=[_contract_to_schema(contract) for contract in hub_contracts],
            )
    except FinanceDataHubError:
        pass
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


@router.get("/quotes/history", response_model=OptionQuoteHistoryResponse)
def get_option_quote_history(
    option_symbol: str = Query(min_length=1, max_length=128),
    limit: int = Query(default=50, ge=1, le=500),
    session: Session = Depends(get_db_session),
) -> OptionQuoteHistoryResponse:
    normalized_symbol = option_symbol.upper()
    runtime_settings = resolve_runtime_settings(session)
    try:
        quotes = FinanceDataHubClient(runtime_settings.finance_data_hub_base_url).list_option_quote_history(
            provider_symbol=normalized_symbol,
            limit=limit,
        )
    except FinanceDataHubError:
        quotes = []
    return OptionQuoteHistoryResponse(
        option_symbol=normalized_symbol,
        quotes=[_snapshot_to_schema(quote) for quote in quotes],
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


def next_friday(today: date | None = None) -> date:
    current = today or date.today()
    days_until_friday = (4 - current.weekday()) % 7
    if days_until_friday == 0:
        days_until_friday = 7
    return date.fromordinal(current.toordinal() + days_until_friday)


def _nearest_hub_expiry(rows: list[dict]) -> date | None:
    expiries = set()
    for row in rows:
        raw_expiry = row.get("expiration_date") or row.get("expiry")
        if raw_expiry:
            expiries.add(date.fromisoformat(str(raw_expiry)[:10]))
    return min(expiries) if expiries else None
