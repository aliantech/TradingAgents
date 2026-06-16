def latest_quote_key(symbol: str) -> str:
    return f"latest:{symbol.upper()}"


def option_chain_key(underlying: str, expiry: str) -> str:
    return f"chain:{underlying.upper()}:{expiry}"


def analysis_progress_key(analysis_id: str) -> str:
    return f"task:{analysis_id}:progress"


MARKET_EVENTS_STREAM = "stream:market_events"
SIGNALS_STREAM = "stream:signals"
