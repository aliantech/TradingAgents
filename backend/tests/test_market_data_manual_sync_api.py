from datetime import UTC, date, datetime, timedelta

from fastapi.testclient import TestClient

from app.db.session import SessionLocal, initialize_database
from app.main import app
from app.market_data.repository import MarketDataRepository
from app.market_data.schemas import MarketBar
from app.market_data.sync_repository import ProviderSyncRepository


class FixtureMarketDataProvider:
    def fetch_bars(self, symbol: str, timeframe: str, start: date, end: date) -> list[MarketBar]:
        return self.fetch_daily_bars(symbol, start, end)

    def fetch_daily_bars(self, symbol: str, start: date, end: date) -> list[MarketBar]:
        days = (end - start).days + 1
        return [
            MarketBar(
                symbol=symbol.upper(),
                timeframe="1d",
                timestamp=datetime.combine(start + timedelta(days=index), datetime.min.time(), tzinfo=UTC),
                open=550.0 + index,
                high=551.0 + index,
                low=549.5 + index,
                close=550.5 + index,
                volume=1000 + index,
                source="fixture",
            )
            for index in range(days)
        ]


def test_manual_sync_api_runs_provider_daily_bars_and_records_audit(monkeypatch):
    from app.market_data import cli

    monkeypatch.setattr(cli, "get_market_data_provider", lambda *args, **kwargs: FixtureMarketDataProvider())
    initialize_database()
    response = TestClient(app).post(
        "/api/market-data/sync-daily-bars",
        json={
            "symbol": "spy",
            "start": "2026-06-16",
            "end": "2026-06-17",
            "provider": "fixture",
        },
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "succeeded"
    assert payload["rows_written"] == 2

    session = SessionLocal()
    try:
        bars = MarketDataRepository(session).list_bars(symbol="SPY", timeframe="1d")
        runs = ProviderSyncRepository(session).list_runs()
    finally:
        session.close()
    assert len(bars) >= 2
    assert any(run.provider == "fixture" and run.status == "succeeded" for run in runs)


def test_manual_sync_api_rejects_when_disabled(monkeypatch):
    from app.market_data import router
    from app.core.config import settings

    monkeypatch.setattr(
        router,
        "resolve_runtime_settings",
        lambda session: settings.model_copy(update={"manual_market_sync_enabled": False}),
    )

    response = TestClient(app).post(
        "/api/market-data/sync-daily-bars",
        json={
            "symbol": "SPY",
            "start": str(date(2026, 6, 16)),
            "end": str(date(2026, 6, 17)),
            "provider": "fixture",
        },
    )

    assert response.status_code == 403
