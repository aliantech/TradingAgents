def latest_quote_key(symbol: str) -> str:
    return f"latest:{symbol.upper()}"


MARKET_EVENTS_STREAM = "stream:market_events"
