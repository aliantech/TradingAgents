from datetime import UTC, date, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.options.repository import OptionContractRecord, OptionRepository, OptionSnapshotRecord


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_option_repository_upserts_contract_and_lists_by_underlying_expiry():
    repository = OptionRepository(_session())
    contract = OptionContractRecord(
        option_symbol="SPY240617C00550000",
        underlying_symbol="SPY",
        expiry=date(2024, 6, 17),
        strike=550.0,
        option_type="call",
        exercise_style="american",
        expiration_type="standard",
        source="finance_data_hub",
    )

    first = repository.upsert_contract(contract)
    second = repository.upsert_contract(
        OptionContractRecord(
            option_symbol="SPY240617C00550000",
            underlying_symbol="SPY",
            expiry=date(2024, 6, 17),
            strike=550.0,
            option_type="call",
            exercise_style="american",
            expiration_type="weekly",
            source="finance_data_hub",
        )
    )

    contracts = repository.list_contracts(underlying_symbol="spy", expiry=date(2024, 6, 17))
    assert first.id == second.id
    assert len(contracts) == 1
    assert contracts[0].option_symbol == "SPY240617C00550000"
    assert contracts[0].underlying_symbol == "SPY"
    assert contracts[0].expiration_type == "weekly"


def test_option_repository_upserts_snapshots_and_lists_chain():
    repository = OptionRepository(_session())
    contract = repository.upsert_contract(
        OptionContractRecord(
            option_symbol="SPY240617P00540000",
            underlying_symbol="SPY",
            expiry=date(2024, 6, 17),
            strike=540.0,
            option_type="put",
            exercise_style="american",
            expiration_type="standard",
            source="finance_data_hub",
        )
    )
    timestamp = datetime(2024, 6, 17, 13, 30, tzinfo=UTC)

    repository.upsert_snapshot(
        OptionSnapshotRecord(
            option_symbol=contract.option_symbol,
            underlying_symbol=contract.underlying_symbol,
            timestamp=timestamp,
            bid=1.1,
            ask=1.2,
            last=1.15,
            volume=100,
            open_interest=1200,
            implied_volatility=0.22,
            delta=-0.35,
            gamma=0.018,
            theta=-0.12,
            vega=0.31,
            source="finance_data_hub",
        )
    )
    repository.upsert_snapshot(
        OptionSnapshotRecord(
            option_symbol=contract.option_symbol,
            underlying_symbol=contract.underlying_symbol,
            timestamp=timestamp,
            bid=1.3,
            ask=1.4,
            last=1.35,
            volume=150,
            open_interest=1250,
            implied_volatility=0.23,
            delta=-0.36,
            gamma=0.019,
            theta=-0.13,
            vega=0.32,
            source="finance_data_hub",
        )
    )

    snapshots = repository.list_chain_snapshots(underlying_symbol="SPY", expiry=date(2024, 6, 17))
    assert len(snapshots) == 1
    assert snapshots[0].option_symbol == "SPY240617P00540000"
    assert snapshots[0].bid == 1.3
    assert snapshots[0].volume == 150
    assert snapshots[0].source == "finance_data_hub"
