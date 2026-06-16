from datetime import date

from fastapi.testclient import TestClient

from app.db.session import SessionLocal, initialize_database
from app.main import app
from app.market_data.repository import MarketDataRepository
from app.market_data.sync_repository import ProviderSyncRepository


def test_manual_sync_api_runs_sample_daily_bars_and_records_audit():
    initialize_database()
    response = TestClient(app).post(
        "/api/market-data/sync-daily-bars",
        json={
            "symbol": "spy",
            "start": "2026-06-16",
            "end": "2026-06-17",
            "provider": "sample",
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
    assert any(run.provider == "sample" and run.status == "succeeded" for run in runs)


def test_manual_sync_api_rejects_when_disabled(monkeypatch):
    from app.market_data import router

    monkeypatch.setattr(router.settings, "manual_market_sync_enabled", False)

    response = TestClient(app).post(
        "/api/market-data/sync-daily-bars",
        json={
            "symbol": "SPY",
            "start": str(date(2026, 6, 16)),
            "end": str(date(2026, 6, 17)),
            "provider": "sample",
        },
    )

    assert response.status_code == 403
