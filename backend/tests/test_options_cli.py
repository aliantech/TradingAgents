import json
from datetime import UTC, date, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.market_data.sync_repository import ProviderSyncRepository
from app.options import cli
from app.options.polygon_provider import OptionChainProviderRecord
from app.options.repository import OptionContractRecord, OptionRepository, OptionSnapshotRecord


class FakeOptionChainProvider:
    def fetch_chain_snapshot(
        self,
        underlying_symbol: str,
        *,
        expiry: date,
        limit: int,
    ) -> list[OptionChainProviderRecord]:
        return [
            OptionChainProviderRecord(
                contract=OptionContractRecord(
                    option_symbol="O:SPY240621C00550000",
                    underlying_symbol=underlying_symbol,
                    expiry=expiry,
                    strike=550.0,
                    option_type="call",
                    exercise_style="american",
                    expiration_type="weekly",
                    source="polygon",
                ),
                snapshot=OptionSnapshotRecord(
                    option_symbol="O:SPY240621C00550000",
                    underlying_symbol=underlying_symbol,
                    timestamp=datetime(2024, 6, 17, 13, 30, tzinfo=UTC),
                    bid=4.2,
                    ask=4.4,
                    last=4.3,
                    volume=220,
                    open_interest=1200,
                    implied_volatility=0.19,
                    delta=0.42,
                    gamma=0.018,
                    theta=-0.09,
                    vega=0.21,
                    source="polygon",
                ),
            )
        ]


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_options_cli_run_sync_chain_uses_service_and_records_audit():
    session = _session()

    result = cli.run_sync_chain(
        session=session,
        provider=FakeOptionChainProvider(),
        provider_name="polygon",
        underlying_symbol="spy",
        expiry=date(2024, 6, 21),
        limit=25,
    )

    assert result.status == "succeeded"
    assert result.rows_written == 1
    assert result.underlying_symbol == "SPY"
    assert OptionRepository(session).list_chain_snapshots(underlying_symbol="SPY", expiry=date(2024, 6, 21))
    assert ProviderSyncRepository(session).list_runs(provider="polygon", sync_type="options_chain")


def test_options_cli_main_returns_not_ready_without_api_key(monkeypatch, capsys):
    monkeypatch.setattr(cli.settings, "polygon_api_key", "")

    exit_code = cli.main(["sync-chain", "--underlying", "SPX", "--expiry", "2024-06-21", "--provider", "polygon"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 1
    assert payload["status"] == "not_ready"
    assert payload["readiness_ready"] is False
    assert payload["missing"] == ["AQUANTLENS_POLYGON_API_KEY"]
