from datetime import datetime, timezone

from fastapi import APIRouter, Query

from app.options.schemas import OptionChainResponse, OptionSnapshot

router = APIRouter(prefix="/api/options", tags=["options"])


def _sample_snapshots(underlying: str) -> list[OptionSnapshot]:
    timestamp = datetime(2026, 6, 17, 13, 30, tzinfo=timezone.utc)
    strikes = [5900, 5950, 6000, 6050, 6100]
    snapshots: list[OptionSnapshot] = []
    for index, strike in enumerate(strikes):
        snapshots.append(
            OptionSnapshot(
                option_symbol=f"{underlying}W260617C{strike:08d}",
                underlying_symbol=underlying,
                timestamp=timestamp,
                bid=8.5 + index * 1.2,
                ask=8.9 + index * 1.2,
                last=8.7 + index * 1.2,
                volume=1200 - index * 90,
                open_interest=8000 + index * 350,
                implied_volatility=0.18 + index * 0.006,
                delta=0.35 + index * 0.06,
                gamma=0.018 + index * 0.001,
                theta=-0.14 - index * 0.01,
                vega=0.31 + index * 0.02,
                source="sample",
            )
        )
    return snapshots


@router.get("/chain", response_model=OptionChainResponse)
def get_option_chain(
    underlying: str = Query(default="SPX", min_length=1, max_length=32),
    expiry: str = Query(default="2026-06-17", min_length=10, max_length=10),
) -> OptionChainResponse:
    normalized_underlying = underlying.upper()
    return OptionChainResponse(
        underlying_symbol=normalized_underlying,
        expiry=expiry,
        snapshots=_sample_snapshots(normalized_underlying),
    )
