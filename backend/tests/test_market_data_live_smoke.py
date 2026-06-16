from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings
from app.db.base import Base
from app.market_data import cli
from app.market_data.sync import MarketDataSyncResult


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_live_provider_smoke_refuses_to_run_when_provider_is_not_ready(monkeypatch):
    session = _session()
    calls = []

    monkeypatch.setattr(cli, "settings", Settings(market_data_provider="polygon", polygon_api_key=""))
    monkeypatch.setattr(cli, "run_sync_bars", lambda **kwargs: calls.append(kwargs))

    result = cli.run_live_provider_smoke(
        session=session,
        provider_name="polygon",
        symbol="SPY",
        timeframe="1d",
        start=date(2026, 6, 17),
        end=date(2026, 6, 17),
    )

    assert result.status == "not_ready"
    assert result.rows_written == 0
    assert result.provider == "polygon"
    assert result.symbol == "SPY"
    assert result.timeframe == "1d"
    assert result.missing == ["AQUANTLENS_POLYGON_API_KEY"]
    assert calls == []


def test_live_provider_smoke_runs_bounded_sync_when_provider_is_ready(monkeypatch):
    session = _session()
    calls = []

    monkeypatch.setattr(cli, "settings", Settings(market_data_provider="polygon", polygon_api_key="secret-value"))

    def fake_run_sync_bars(**kwargs):
        calls.append(kwargs)
        return MarketDataSyncResult(status="succeeded", rows_written=1)

    monkeypatch.setattr(cli, "run_sync_bars", fake_run_sync_bars)

    result = cli.run_live_provider_smoke(
        session=session,
        provider_name="polygon",
        symbol="spy",
        timeframe="1d",
        start=date(2026, 6, 17),
        end=date(2026, 6, 17),
    )

    assert result.status == "succeeded"
    assert result.rows_written == 1
    assert result.provider == "polygon"
    assert result.symbol == "SPY"
    assert result.timeframe == "1d"
    assert result.missing == []
    assert calls == [
        {
            "session": session,
            "provider_name": "polygon",
            "symbol": "SPY",
            "timeframe": "1d",
            "start": date(2026, 6, 17),
            "end": date(2026, 6, 17),
        }
    ]
    assert "secret-value" not in repr(result)


def test_cli_live_provider_smoke_prints_sanitized_not_ready_payload(monkeypatch, capsys):
    session = _session()

    monkeypatch.setattr(cli, "settings", Settings(market_data_provider="polygon", polygon_api_key=""))
    monkeypatch.setattr(cli, "initialize_database", lambda: None)
    monkeypatch.setattr(cli, "SessionLocal", lambda: session)

    exit_code = cli.main(
        [
            "live-provider-smoke",
            "--provider",
            "polygon",
            "--symbol",
            "SPY",
            "--timeframe",
            "1d",
            "--start",
            "2026-06-17",
            "--end",
            "2026-06-17",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert '"status": "not_ready"' in output
    assert "AQUANTLENS_POLYGON_API_KEY" in output
    assert "apiKey" not in output
