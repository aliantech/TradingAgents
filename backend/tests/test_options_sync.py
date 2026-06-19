from datetime import UTC, date, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.market_data.sync_repository import ProviderSyncRepository
from app.options.polygon_provider import OptionChainProviderRecord
from app.options.repository import OptionContractRecord, OptionRepository, OptionSnapshotRecord
from app.options.sync import OptionChainSyncService


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


class EmptyOptionChainProvider:
    def fetch_chain_snapshot(
        self,
        underlying_symbol: str,
        *,
        expiry: date,
        limit: int,
    ) -> list[OptionChainProviderRecord]:
        return []


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_option_chain_sync_service_persists_contracts_snapshots_and_audit_run():
    session = _session()
    service = OptionChainSyncService(
        provider=FakeOptionChainProvider(),
        provider_name="polygon",
        option_repository=OptionRepository(session),
        sync_repository=ProviderSyncRepository(session),
    )

    result = service.sync_chain(underlying_symbol="SPY", expiry=date(2024, 6, 21), limit=25)

    assert result.status == "succeeded"
    assert result.rows_written == 1
    snapshots = OptionRepository(session).list_chain_snapshots(
        underlying_symbol="SPY",
        expiry=date(2024, 6, 21),
    )
    assert len(snapshots) == 1
    assert snapshots[0].bid == 4.2
    runs = ProviderSyncRepository(session).list_runs(provider="polygon", sync_type="options_chain")
    assert len(runs) == 1
    assert runs[0].status == "succeeded"
    assert runs[0].target_symbol == "SPY"
    assert runs[0].target_expiry == date(2024, 6, 21)
    assert runs[0].rows_written == 1


def test_option_chain_sync_service_marks_empty_chain_as_empty_audit_run():
    session = _session()
    service = OptionChainSyncService(
        provider=EmptyOptionChainProvider(),
        provider_name="polygon",
        option_repository=OptionRepository(session),
        sync_repository=ProviderSyncRepository(session),
    )

    result = service.sync_chain(underlying_symbol="SPX", expiry=date(2024, 6, 21), limit=25)

    assert result.status == "empty"
    assert result.rows_written == 0
    runs = ProviderSyncRepository(session).list_runs(provider="polygon", sync_type="options_chain")
    assert len(runs) == 1
    assert runs[0].status == "empty"
    assert runs[0].target_symbol == "SPX"
    assert runs[0].target_expiry == date(2024, 6, 21)
    assert runs[0].rows_written == 0
