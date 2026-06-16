from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.options.repository import OptionRepository, OptionSnapshotRecord
from app.options.sample_data import seed_sample_option_chain
from app.options.schemas import OptionChainResponse, OptionSnapshot

router = APIRouter(prefix="/api/options", tags=["options"])


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
