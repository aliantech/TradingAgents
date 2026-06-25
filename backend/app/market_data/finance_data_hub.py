from datetime import UTC, date, datetime
from urllib.parse import urlencode
from urllib.request import urlopen

from app.market_data.schemas import MarketBar
from app.options.repository import OptionSnapshotRecord


class FinanceDataHubError(RuntimeError):
    pass


class FinanceDataHubClient:
    def __init__(self, base_url: str, *, transport=None) -> None:
        self.base_url = base_url.rstrip("/")
        self.transport = transport or UrlLibTransport()

    def list_bars(
        self,
        *,
        symbol: str,
        timeframe: str,
        start: date | None = None,
        end: date | None = None,
    ) -> list[MarketBar]:
        query = {"timeframe": timeframe}
        if start is not None:
            query["start"] = start.isoformat()
        if end is not None:
            query["end"] = end.isoformat()
        payload = self.transport.get_json(f"{self.base_url}/assets/{symbol.upper()}/bars?{urlencode(query)}")
        if not isinstance(payload, list):
            raise FinanceDataHubError("Finance Data Hub bars response must be a list.")
        return [_bar_from_hub_row(symbol.upper(), timeframe, row) for row in payload]

    def list_option_latest_quotes(
        self,
        *,
        underlying_symbol: str,
        expiry: date | None = None,
    ) -> list[OptionSnapshotRecord]:
        query = {"expiration_date": expiry.isoformat()} if expiry is not None else {}
        payload = self.transport.get_json(
            f"{self.base_url}/options/quotes/latest/{underlying_symbol.upper()}?{urlencode(query)}"
        )
        rows = payload.get("quotes") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            raise FinanceDataHubError("Finance Data Hub option quotes response must include quotes list.")
        return [_option_snapshot_from_hub_row(underlying_symbol.upper(), row) for row in rows]

    def list_option_latest_quote_rows(
        self,
        *,
        underlying_symbol: str,
        expiry: date | None = None,
    ) -> list[dict]:
        query = {"expiration_date": expiry.isoformat()} if expiry is not None else {}
        payload = self.transport.get_json(
            f"{self.base_url}/options/quotes/latest/{underlying_symbol.upper()}?{urlencode(query)}"
        )
        rows = payload.get("quotes") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            raise FinanceDataHubError("Finance Data Hub option quotes response must include quotes list.")
        return [dict(row) for row in rows]


class UrlLibTransport:
    def get_json(self, url: str) -> object:
        import json

        try:
            with urlopen(url, timeout=5) as response:  # noqa: S310 - URL comes from operator-controlled runtime config.
                return json.loads(response.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001 - callers fall back to local read-only data.
            raise FinanceDataHubError(str(exc)) from exc


def _bar_from_hub_row(symbol: str, timeframe: str, row: dict) -> MarketBar:
    return MarketBar(
        symbol=str(row.get("symbol") or row.get("asset_id") or symbol).upper(),
        timeframe=str(row.get("timeframe") or timeframe),
        timestamp=_parse_datetime(row.get("timestamp") or row.get("ts") or row.get("datetime")),
        open=float(row["open"]),
        high=float(row["high"]),
        low=float(row["low"]),
        close=float(row["close"]),
        volume=int(row.get("volume") or 0),
        source=str(row.get("source") or "finance_data_hub"),
    )


def _option_snapshot_from_hub_row(underlying_symbol: str, row: dict) -> OptionSnapshotRecord:
    option_symbol = str(row.get("provider_symbol") or row.get("occ_symbol") or row.get("option_symbol")).upper()
    return OptionSnapshotRecord(
        option_symbol=option_symbol,
        underlying_symbol=underlying_symbol,
        timestamp=_parse_datetime(row.get("provider_timestamp") or row.get("timestamp")),
        bid=_optional_float(row.get("bid")),
        ask=_optional_float(row.get("ask")),
        last=_optional_float(row.get("last") or row.get("mid")),
        volume=int(row.get("volume") or 0),
        open_interest=_optional_int(row.get("open_interest")),
        implied_volatility=_optional_float(row.get("implied_volatility") or row.get("iv")),
        delta=_optional_float(row.get("delta")),
        gamma=_optional_float(row.get("gamma")),
        theta=_optional_float(row.get("theta")),
        vega=_optional_float(row.get("vega")),
        source=str(row.get("source") or "finance_data_hub"),
    )


def _parse_datetime(value: object) -> datetime:
    if value is None:
        raise FinanceDataHubError("Finance Data Hub row is missing timestamp.")
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _optional_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    return int(value)
