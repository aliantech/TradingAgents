from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Protocol
from urllib.parse import urlencode

from app.market_data.polygon_provider import JsonTransport, UrlLibJsonTransport
from app.options.repository import OptionContractRecord, OptionSnapshotRecord


@dataclass(frozen=True)
class OptionChainProviderRecord:
    contract: OptionContractRecord
    snapshot: OptionSnapshotRecord


class OptionChainProvider(Protocol):
    def fetch_chain_snapshot(
        self,
        underlying_symbol: str,
        *,
        expiry: date,
        limit: int,
    ) -> list[OptionChainProviderRecord]:
        pass


class PolygonOptionsProvider:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str = "https://api.polygon.io",
        transport: JsonTransport | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("AQUANTLENS_POLYGON_API_KEY is required for polygon options provider.")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.transport = transport or UrlLibJsonTransport()

    def fetch_chain_snapshot(
        self,
        underlying_symbol: str,
        *,
        expiry: date,
        limit: int,
    ) -> list[OptionChainProviderRecord]:
        underlying = underlying_symbol.upper()
        query = urlencode(
            {
                "expiration_date": expiry.isoformat(),
                "limit": limit,
                "apiKey": self.api_key,
            }
        )
        payload = self.transport.get_json(f"{self.base_url}/v3/snapshot/options/{underlying}?{query}")
        return [_snapshot_record(row, fallback_underlying=underlying, fallback_expiry=expiry) for row in payload.get("results", [])]


def _snapshot_record(row: dict, *, fallback_underlying: str, fallback_expiry: date) -> OptionChainProviderRecord:
    details = row.get("details") or {}
    greeks = row.get("greeks") or {}
    last_quote = row.get("last_quote") or {}
    last_trade = row.get("last_trade") or {}
    day = row.get("day") or {}
    option_symbol = str(details.get("ticker") or "").upper()
    underlying = str(details.get("underlying_ticker") or fallback_underlying).upper()
    expiry = date.fromisoformat(str(details.get("expiration_date") or fallback_expiry.isoformat()))
    timestamp = _timestamp_from_snapshot(row, last_quote, last_trade)
    contract = OptionContractRecord(
        option_symbol=option_symbol,
        underlying_symbol=underlying,
        expiry=expiry,
        strike=float(details.get("strike_price") or 0),
        option_type=str(details.get("contract_type") or "").lower(),
        exercise_style=details.get("exercise_style"),
        expiration_type=details.get("expiration_type"),
        source="polygon",
    )
    snapshot = OptionSnapshotRecord(
        option_symbol=option_symbol,
        underlying_symbol=underlying,
        timestamp=timestamp,
        bid=_optional_float(last_quote.get("bid")),
        ask=_optional_float(last_quote.get("ask")),
        last=_optional_float(last_trade.get("price")),
        volume=int(day.get("volume") or row.get("volume") or 0),
        open_interest=_optional_int(row.get("open_interest")),
        implied_volatility=_optional_float(row.get("implied_volatility")),
        delta=_optional_float(greeks.get("delta")),
        gamma=_optional_float(greeks.get("gamma")),
        theta=_optional_float(greeks.get("theta")),
        vega=_optional_float(greeks.get("vega")),
        source="polygon",
    )
    return OptionChainProviderRecord(contract=contract, snapshot=snapshot)


def _timestamp_from_snapshot(row: dict, last_quote: dict, last_trade: dict) -> datetime:
    value = last_quote.get("last_updated") or last_trade.get("sip_timestamp") or row.get("updated")
    if isinstance(value, int):
        if value > 10_000_000_000_000:
            return datetime.fromtimestamp(value / 1_000_000_000, tz=UTC)
        return datetime.fromtimestamp(value / 1000, tz=UTC)
    return datetime.now(tz=UTC)


def _optional_float(value) -> float | None:
    return None if value is None else float(value)


def _optional_int(value) -> int | None:
    return None if value is None else int(value)
