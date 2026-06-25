from app.realtime.cache_keys import (
    MARKET_EVENTS_STREAM,
    latest_quote_key,
)


def test_realtime_cache_keys_are_stable():
    assert latest_quote_key("spy") == "latest:SPY"
    assert MARKET_EVENTS_STREAM == "stream:market_events"
