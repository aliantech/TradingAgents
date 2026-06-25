from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.market_data import cli
from app.market_data.sync_repository import ProviderSyncRepository


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_cli_list_sync_runs_outputs_sanitized_audit_rows(monkeypatch, capsys):
    session = _session()
    started_at = datetime(2026, 6, 17, 13, 30, tzinfo=UTC)
    repository = ProviderSyncRepository(session)
    repository.record_run(
        provider="finance_data_hub",
        sync_type="daily_bars",
        status="succeeded",
        started_at=started_at,
        finished_at=started_at + timedelta(seconds=2),
        rows_written=1,
    )
    repository.record_run(
        provider="fixture",
        sync_type="bars_1m",
        status="failed",
        started_at=started_at + timedelta(minutes=1),
        finished_at=started_at + timedelta(minutes=1, seconds=3),
        rows_written=0,
        error_message="fixture timeout",
    )
    monkeypatch.setattr(cli, "initialize_database", lambda: None)
    monkeypatch.setattr(cli, "SessionLocal", lambda: session)

    exit_code = cli.main(
        ["list-sync-runs", "--provider", "finance_data_hub", "--sync-type", "daily_bars", "--limit", "5"]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert '"provider": "finance_data_hub"' in output
    assert '"sync_type": "daily_bars"' in output
    assert '"status": "succeeded"' in output
    assert '"rows_written": 1' in output
    assert '"fixture timeout"' not in output


def test_cli_list_sync_runs_redacts_secret_like_error_messages(monkeypatch, capsys):
    session = _session()
    started_at = datetime(2026, 6, 17, 13, 30, tzinfo=UTC)
    ProviderSyncRepository(session).record_run(
        provider="finance_data_hub",
        sync_type="daily_bars",
        status="failed",
        started_at=started_at,
        finished_at=started_at + timedelta(seconds=2),
        rows_written=0,
        error_message="request failed: https://hub.test/bars?apiKey=secret-value",
    )
    monkeypatch.setattr(cli, "initialize_database", lambda: None)
    monkeypatch.setattr(cli, "SessionLocal", lambda: session)

    exit_code = cli.main(["list-sync-runs", "--provider", "finance_data_hub", "--sync-type", "daily_bars"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "secret-value" not in output
    assert "apiKey=***" in output
