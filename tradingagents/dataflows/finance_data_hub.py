"""Finance Data Hub market-data dataflow."""

from datetime import datetime
from typing import Annotated
import json
import os
import urllib.parse
import urllib.request

import pandas as pd

from .stockstats_utils import _assert_ohlcv_not_stale
from .symbol_utils import NoMarketDataError

DEFAULT_BASE_URL = "http://127.0.0.1:18180"


def get_finance_data_hub_data_online(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    datetime.strptime(start_date, "%Y-%m-%d")
    datetime.strptime(end_date, "%Y-%m-%d")
    data = _download_finance_data_hub_frame(symbol.upper(), start_date, end_date)
    if data.empty:
        raise NoMarketDataError(symbol, symbol.upper(), f"no rows between {start_date} and {end_date}")

    _assert_ohlcv_not_stale(data, end_date, symbol, symbol.upper())

    for col in ["Open", "High", "Low", "Close", "Adj Close"]:
        if col in data.columns:
            data[col] = data[col].round(2)

    header = f"# Stock data for {symbol.upper()} from {start_date} to {end_date}\n"
    header += f"# Total records: {len(data)}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    header += "# Data source: Finance Data Hub\n\n"
    return header + data.to_csv()


def _download_finance_data_hub_frame(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    base_url = _base_url()
    asset = _fetch_json(f"{base_url}/assets/{urllib.parse.quote(symbol)}")
    asset_id = _asset_id(asset)
    query = urllib.parse.urlencode({"timeframe": "1d", "start": start_date, "end": end_date})
    payload = _fetch_json(f"{base_url}/assets/{urllib.parse.quote(asset_id)}/bars?{query}")
    rows = payload.get("bars") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise NoMarketDataError(symbol, symbol, "Finance Data Hub bars response must be a list.")
    return _bars_to_frame(rows)


def _asset_id(payload: object) -> str:
    asset = payload.get("asset") if isinstance(payload, dict) else None
    source = asset if isinstance(asset, dict) else payload
    if isinstance(source, dict):
        value = source.get("asset_id") or source.get("id")
        if value:
            return str(value)
    raise NoMarketDataError("UNKNOWN", "UNKNOWN", "Finance Data Hub asset response is missing asset_id.")


def _fetch_json(url: str) -> object:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AQuantLens-TradingAgents",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def _base_url() -> str:
    try:
        from .config import get_config

        configured = get_config().get("finance_data_hub_base_url")
    except Exception:  # noqa: BLE001 - fall back to env/default if config is not initialized
        configured = None
    return str(configured or os.getenv("AQUANTLENS_FINANCE_DATA_HUB_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")


def _bars_to_frame(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    frame = pd.DataFrame(
        {
            "Date": pd.to_datetime([row.get("timestamp") for row in rows], errors="coerce", utc=True),
            "Open": [_float_value(row.get("open")) for row in rows],
            "High": [_float_value(row.get("high")) for row in rows],
            "Low": [_float_value(row.get("low")) for row in rows],
            "Close": [_float_value(row.get("close")) for row in rows],
            "Volume": [_int_value(row.get("volume")) for row in rows],
        }
    )
    frame = frame.dropna(subset=["Date", "Open", "High", "Low", "Close"], how="any")
    if frame.empty:
        return frame
    frame["Date"] = frame["Date"].dt.tz_convert(None).dt.normalize()
    frame["Adj Close"] = frame["Close"]
    return frame.sort_values("Date").set_index("Date")


def _float_value(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def _int_value(value: object) -> int:
    if value is None:
        return 0
    return int(float(value))
