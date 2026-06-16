from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.db.session import SessionLocal, initialize_database
from app.main import app
from app.market_data.sync_repository import ProviderSyncRepository


def test_market_data_sync_runs_api_lists_recent_runs():
    initialize_database()
    session = SessionLocal()
    try:
        recorded = ProviderSyncRepository(session).record_run(
            provider="unit-test-provider",
            sync_type="daily_bars",
            status="succeeded",
            started_at=datetime(2026, 6, 17, 13, 30, tzinfo=timezone.utc),
            finished_at=datetime(2026, 6, 17, 13, 31, tzinfo=timezone.utc),
            rows_written=3,
        )
    finally:
        session.close()

    response = TestClient(app).get("/api/market-data/sync-runs")

    assert response.status_code == 200
    payload = response.json()
    assert any(item["id"] == str(recorded.id) for item in payload["runs"])
    matched = next(item for item in payload["runs"] if item["id"] == str(recorded.id))
    assert matched["provider"] == "unit-test-provider"
    assert matched["sync_type"] == "daily_bars"
    assert matched["status"] == "succeeded"
    assert matched["rows_written"] == 3
