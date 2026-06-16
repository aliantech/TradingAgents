from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.session import SessionLocal, initialize_database
from app.main import app
from app.market_data.sync_repository import ProviderSyncRepository


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _record_sample_runs(repository: ProviderSyncRepository) -> None:
    started_at = datetime(2026, 6, 17, 13, 30, tzinfo=UTC)
    repository.record_run(
        provider="sample",
        sync_type="bars_1m",
        status="succeeded",
        started_at=started_at,
        finished_at=started_at + timedelta(seconds=2),
        rows_written=10,
    )
    repository.record_run(
        provider="sample",
        sync_type="bars_1m",
        status="failed",
        started_at=started_at + timedelta(minutes=1),
        finished_at=started_at + timedelta(minutes=1, seconds=4),
        rows_written=0,
        error_message="timeout",
    )


def test_provider_sync_repository_summarizes_runs():
    repository = ProviderSyncRepository(_session())
    _record_sample_runs(repository)

    summary = repository.summarize_runs()

    assert summary.total_runs == 2
    assert summary.succeeded == 1
    assert summary.failed == 1
    assert summary.rows_written == 10
    assert summary.latest_status == "failed"
    assert summary.average_duration_ms == 3000


def test_sync_summary_api_returns_health_metrics():
    initialize_database()
    session = SessionLocal()
    try:
        _record_sample_runs(ProviderSyncRepository(session))
    finally:
        session.close()

    response = TestClient(app).get("/api/market-data/sync-summary")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_runs"] >= 2
    assert payload["succeeded"] >= 1
    assert payload["failed"] >= 1
    assert payload["rows_written"] >= 10
    assert payload["latest_status"] in {"failed", "succeeded"}
    assert payload["average_duration_ms"] >= 0
