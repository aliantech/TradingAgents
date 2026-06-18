from datetime import UTC, date, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.market_data import cli
from app.market_data.cli import run_sync_bars, run_sync_daily_bars
from app.market_data.repository import MarketDataRepository
from app.market_data.sync_repository import ProviderSyncRepository
from app.market_data.cli import LiveProviderSmokeResult
from app.market_data.schemas import MarketBar


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


class FixtureMarketDataProvider:
    def fetch_bars(self, symbol: str, timeframe: str, start: date, end: date) -> list[MarketBar]:
        return self.fetch_daily_bars(symbol, start, end) if timeframe == "1d" else [
            MarketBar(
                symbol=symbol.upper(),
                timeframe=timeframe,
                timestamp=datetime(2026, 6, 17, 13, 30, tzinfo=UTC),
                open=550.0,
                high=551.0,
                low=549.5,
                close=550.5,
                volume=1000,
                source="fixture",
            )
        ]

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


def use_fixture_provider(monkeypatch):
    monkeypatch.setattr(cli, "get_market_data_provider", lambda *args, **kwargs: FixtureMarketDataProvider())


def test_run_sync_daily_bars_uses_configured_provider_and_records_audit(monkeypatch):
    session = _session()
    use_fixture_provider(monkeypatch)

    result = run_sync_daily_bars(
        session=session,
        provider_name="fixture",
        symbol="spy",
        start=date(2026, 6, 16),
        end=date(2026, 6, 17),
    )

    bars = MarketDataRepository(session).list_bars(symbol="SPY", timeframe="1d")
    runs = ProviderSyncRepository(session).list_runs()
    assert result.status == "succeeded"
    assert result.rows_written == 2
    assert len(bars) == 2
    assert bars[0].symbol == "SPY"
    assert bars[0].source == "fixture"
    assert len(runs) == 1
    assert runs[0].provider == "fixture"
    assert runs[0].status == "succeeded"


def test_run_sync_daily_bars_publishes_when_realtime_enabled(monkeypatch):
    session = _session()
    published = []
    use_fixture_provider(monkeypatch)

    class FakePublisher:
        def publish_bar(self, bar):
            published.append(bar)

    monkeypatch.setattr("app.market_data.cli.create_market_data_publisher", lambda **kwargs: FakePublisher())
    monkeypatch.setattr("app.market_data.cli.settings.realtime_market_publish_enabled", True)

    result = run_sync_daily_bars(
        session=session,
        provider_name="fixture",
        symbol="SPY",
        start=date(2026, 6, 17),
        end=date(2026, 6, 17),
    )

    assert result.status == "succeeded"
    assert len(published) == 1
    assert published[0].symbol == "SPY"


def test_run_sync_bars_supports_intraday_timeframe(monkeypatch):
    session = _session()
    use_fixture_provider(monkeypatch)

    result = run_sync_bars(
        session=session,
        provider_name="fixture",
        symbol="SPY",
        timeframe="5m",
        start=date(2026, 6, 17),
        end=date(2026, 6, 17),
    )

    bars = MarketDataRepository(session).list_bars(symbol="SPY", timeframe="5m")
    assert result.status == "succeeded"
    assert result.rows_written == 1
    assert len(bars) == 1


def test_cli_run_scheduler_once_outputs_each_target(monkeypatch, capsys):
    session = _session()
    use_fixture_provider(monkeypatch)
    monkeypatch.setattr(cli, "initialize_database", lambda: None)
    monkeypatch.setattr(cli, "SessionLocal", lambda: session)

    exit_code = cli.main(
        [
            "run-scheduler-once",
            "--provider",
            "fixture",
            "--targets",
            "SPY:1d:2,QQQ:5m:1",
            "--today",
            "2026-06-17",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert '"symbol": "SPY"' in output
    assert '"timeframe": "5m"' in output
    assert len(ProviderSyncRepository(session).list_runs()) == 2


def test_cli_run_scheduler_loop_supports_limited_iterations(monkeypatch, capsys):
    session = _session()
    use_fixture_provider(monkeypatch)
    monkeypatch.setattr(cli, "initialize_database", lambda: None)
    monkeypatch.setattr(cli, "SessionLocal", lambda: session)

    exit_code = cli.main(
        [
            "run-scheduler-loop",
            "--provider",
            "fixture",
            "--targets",
            "SPY:1d:2",
            "--today",
            "2026-06-17",
            "--interval-seconds",
            "1",
            "--max-iterations",
            "1",
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert '"iteration": 1' in output
    assert '"rows_written": 2' in output
    assert len(ProviderSyncRepository(session).list_runs()) == 1


def test_cli_list_sync_runs_outputs_sanitized_audit_rows(monkeypatch, capsys):
    session = _session()
    started_at = datetime(2026, 6, 17, 13, 30, tzinfo=UTC)
    repository = ProviderSyncRepository(session)
    repository.record_run(
        provider="polygon",
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

    exit_code = cli.main(["list-sync-runs", "--provider", "polygon", "--sync-type", "daily_bars", "--limit", "5"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert '"provider": "polygon"' in output
    assert '"sync_type": "daily_bars"' in output
    assert '"status": "succeeded"' in output
    assert '"rows_written": 1' in output
    assert '"fixture timeout"' not in output
    assert "apiKey" not in output


def test_cli_list_sync_runs_redacts_secret_like_error_messages(monkeypatch, capsys):
    session = _session()
    started_at = datetime(2026, 6, 17, 13, 30, tzinfo=UTC)
    ProviderSyncRepository(session).record_run(
        provider="polygon",
        sync_type="daily_bars",
        status="failed",
        started_at=started_at,
        finished_at=started_at + timedelta(seconds=2),
        rows_written=0,
        error_message="request failed: https://api.polygon.io/v2/aggs?apiKey=secret-value&adjusted=true",
    )
    monkeypatch.setattr(cli, "initialize_database", lambda: None)
    monkeypatch.setattr(cli, "SessionLocal", lambda: session)

    exit_code = cli.main(["list-sync-runs", "--provider", "polygon", "--sync-type", "daily_bars"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "secret-value" not in output
    assert "apiKey=***" in output


def test_cli_final_live_smoke_gate_stops_when_provider_is_not_ready(monkeypatch, capsys):
    session = _session()
    calls = []

    monkeypatch.setattr(cli, "settings", cli.settings.__class__(market_data_provider="polygon", polygon_api_key=""))
    monkeypatch.setattr(cli, "initialize_database", lambda: None)
    monkeypatch.setattr(cli, "SessionLocal", lambda: session)
    monkeypatch.setattr(cli, "run_live_provider_smoke", lambda **kwargs: calls.append(kwargs))

    exit_code = cli.main(
        [
            "final-live-smoke-gate",
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
    assert calls == []


def test_cli_final_live_smoke_gate_requires_successful_smoke_and_audit_row(monkeypatch, capsys):
    session = _session()
    started_at = datetime(2026, 6, 17, 13, 30, tzinfo=UTC)

    monkeypatch.setattr(cli, "settings", cli.settings.__class__(market_data_provider="polygon", polygon_api_key="secret-value"))
    monkeypatch.setattr(cli, "initialize_database", lambda: None)
    monkeypatch.setattr(cli, "SessionLocal", lambda: session)

    def fake_live_smoke(**kwargs):
        ProviderSyncRepository(session).record_run(
            provider="polygon",
            sync_type="daily_bars",
            status="succeeded",
            started_at=started_at,
            finished_at=started_at + timedelta(seconds=2),
            rows_written=1,
        )
        return LiveProviderSmokeResult(
            provider="polygon",
            symbol="SPY",
            timeframe="1d",
            start="2026-06-17",
            end="2026-06-17",
            status="succeeded",
            rows_written=1,
            missing=[],
        )

    monkeypatch.setattr(cli, "run_live_provider_smoke", fake_live_smoke)

    exit_code = cli.main(
        [
            "final-live-smoke-gate",
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
    assert exit_code == 0
    assert '"status": "succeeded"' in output
    assert '"readiness_ready": true' in output
    assert '"audit_rows_found": 1' in output
    assert "secret-value" not in output
