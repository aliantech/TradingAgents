"""Direct Yahoo chart endpoint dataflow.

This avoids yfinance's cookie/crumb path while still using Yahoo's public chart
JSON endpoint for bounded research smoke runs.
"""

from datetime import datetime, timezone
from typing import Annotated
import json
import urllib.parse
import urllib.request

import pandas as pd
from dateutil.relativedelta import relativedelta

from .stockstats_utils import _assert_ohlcv_not_stale
from .symbol_utils import NoMarketDataError, normalize_symbol

_CHART_HOSTS = ("query1.finance.yahoo.com", "query2.finance.yahoo.com")


def get_direct_yahoo_chart_data_online(
    symbol: Annotated[str, "ticker symbol of the company"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
) -> str:
    datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    canonical = normalize_symbol(symbol)
    end_inclusive = (end_dt + relativedelta(days=1)).strftime("%Y-%m-%d")
    data = _download_chart_frame(canonical, start_date, end_inclusive)

    if data.empty:
        raise NoMarketDataError(symbol, canonical, f"no rows between {start_date} and {end_date}")

    _assert_ohlcv_not_stale(data, end_date, symbol, canonical)

    for col in ["Open", "High", "Low", "Close", "Adj Close"]:
        if col in data.columns:
            data[col] = data[col].round(2)

    label = canonical if canonical == symbol.upper() else f"{canonical} (from {symbol})"
    header = f"# Stock data for {label} from {start_date} to {end_date}\n"
    header += f"# Total records: {len(data)}\n"
    header += f"# Data retrieved on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    header += "# Data source: Yahoo Finance chart endpoint\n\n"
    return header + data.to_csv()


def _download_chart_frame(symbol: str, start_date: str, end_exclusive: str) -> pd.DataFrame:
    period1 = _unix_timestamp(start_date)
    period2 = _unix_timestamp(end_exclusive)
    params = urllib.parse.urlencode(
        {
            "period1": period1,
            "period2": period2,
            "interval": "1d",
            "events": "history",
        }
    )
    last_error: Exception | None = None
    for host in _CHART_HOSTS:
        url = f"https://{host}/v8/finance/chart/{urllib.parse.quote(symbol)}?{params}"
        try:
            payload = _fetch_json(url)
            return _chart_payload_to_frame(payload, symbol)
        except Exception as error:  # noqa: BLE001 - try query2 when query1 fails
            last_error = error
            continue
    if last_error:
        raise last_error
    return pd.DataFrame()


def _fetch_json(url: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.loads(response.read().decode("utf-8"))


def _chart_payload_to_frame(payload: dict, symbol: str) -> pd.DataFrame:
    chart = payload.get("chart") or {}
    error = chart.get("error")
    if error:
        raise NoMarketDataError(symbol, symbol, str(error))
    results = chart.get("result") or []
    if not results:
        return pd.DataFrame()
    result = results[0]
    timestamps = result.get("timestamp") or []
    quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    adjclose = ((result.get("indicators") or {}).get("adjclose") or [{}])[0]
    if not timestamps:
        return pd.DataFrame()

    frame = pd.DataFrame(
        {
            "Date": pd.to_datetime(timestamps, unit="s").tz_localize("UTC").tz_convert(None),
            "Open": quote.get("open") or [],
            "High": quote.get("high") or [],
            "Low": quote.get("low") or [],
            "Close": quote.get("close") or [],
            "Volume": quote.get("volume") or [],
        }
    )
    adjusted = adjclose.get("adjclose")
    if adjusted:
        frame["Adj Close"] = adjusted
    frame = frame.dropna(subset=["Open", "High", "Low", "Close"], how="any")
    if frame.empty:
        return frame
    frame["Date"] = frame["Date"].dt.normalize()
    frame = frame.set_index("Date")
    return frame


def _unix_timestamp(date_value: str) -> int:
    parsed = datetime.strptime(date_value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(parsed.timestamp())
