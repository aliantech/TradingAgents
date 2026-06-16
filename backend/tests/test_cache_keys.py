from app.realtime.cache_keys import (
    MARKET_EVENTS_STREAM,
    SIGNALS_STREAM,
    analysis_progress_key,
    latest_quote_key,
    option_chain_key,
)


def test_realtime_cache_keys_are_stable():
    assert latest_quote_key("spy") == "latest:SPY"
    assert option_chain_key("spx", "2026-06-17") == "chain:SPX:2026-06-17"
    assert analysis_progress_key("abc") == "task:abc:progress"
    assert MARKET_EVENTS_STREAM == "stream:market_events"
    assert SIGNALS_STREAM == "stream:signals"
