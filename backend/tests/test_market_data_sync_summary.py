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


def test_provider_sync_repository_filters_summary_and_runs():
    repository = ProviderSyncRepository(_session())
    started_at = datetime(2026, 6, 17, 13, 30, tzinfo=UTC)
    repository.record_run(
        provider="sample",
        sync_type="bars_1m",
        status="succeeded",
        started_at=started_at,
        finished_at=started_at + timedelta(seconds=1),
        rows_written=5,
    )
    repository.record_run(
        provider="polygon",
        sync_type="daily_bars",
        status="failed",
        started_at=started_at + timedelta(days=1),
        finished_at=started_at + timedelta(days=1, seconds=3),
        rows_written=0,
    )

    summary = repository.summarize_runs(provider="sample", sync_type="bars_1m", started_after=started_at)
    runs = repository.list_runs(provider="sample", sync_type="bars_1m", started_after=started_at)

    assert summary.total_runs == 1
    assert summary.succeeded == 1
    assert summary.failed == 0
    assert summary.rows_written == 5
    assert len(runs) == 1
    assert runs[0].provider == "sample"
    assert runs[0].sync_type == "bars_1m"


def test_provider_sync_repository_groups_summary_by_provider_and_type():
    repository = ProviderSyncRepository(_session())
    started_at = datetime(2026, 6, 17, 13, 30, tzinfo=UTC)
    repository.record_run(
        provider="sample",
        sync_type="daily_bars",
        status="succeeded",
        started_at=started_at,
        finished_at=started_at + timedelta(seconds=1),
        rows_written=2,
    )
    repository.record_run(
        provider="polygon",
        sync_type="bars_1m",
        status="failed",
        started_at=started_at + timedelta(minutes=1),
        finished_at=started_at + timedelta(minutes=1, seconds=3),
        rows_written=0,
    )

    groups = repository.summarize_groups()

    assert {(group.provider, group.sync_type) for group in groups} == {("sample", "daily_bars"), ("polygon", "bars_1m")}
    sample = next(group for group in groups if group.provider == "sample")
    assert sample.total_runs == 1
    assert sample.succeeded == 1
    assert sample.rows_written == 2


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


def test_sync_summary_api_accepts_filters():
    initialize_database()
    session = SessionLocal()
    try:
        started_at = datetime(2026, 6, 17, 13, 30, tzinfo=UTC)
        ProviderSyncRepository(session).record_run(
            provider="sample",
            sync_type="bars_5m",
            status="succeeded",
            started_at=started_at,
            finished_at=started_at + timedelta(seconds=1),
            rows_written=1,
        )
    finally:
        session.close()

    response = TestClient(app).get("/api/market-data/sync-summary?provider=sample&sync_type=bars_5m")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_runs"] >= 1
    assert payload["succeeded"] >= 1


def test_sync_summary_groups_api_returns_grouped_metrics():
    initialize_database()
    session = SessionLocal()
    try:
        started_at = datetime(2026, 6, 17, 13, 30, tzinfo=UTC)
        ProviderSyncRepository(session).record_run(
            provider="sample",
            sync_type="daily_bars",
            status="succeeded",
            started_at=started_at,
            finished_at=started_at + timedelta(seconds=1),
            rows_written=2,
        )
    finally:
        session.close()

    response = TestClient(app).get("/api/market-data/sync-summary/groups?provider=sample")

    assert response.status_code == 200
    groups = response.json()["groups"]
    assert any(group["provider"] == "sample" and group["sync_type"] == "daily_bars" for group in groups)
