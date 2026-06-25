from datetime import UTC, date, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.analysis import option_chain_context
from app.analysis.option_chain_context import build_option_chain_context
from app.db.base import Base
from app.options.repository import OptionContractRecord, OptionRepository, OptionSnapshotRecord


def _session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _force_hub_unavailable(*args, **kwargs):
    raise option_chain_context.FinanceDataHubError("FDH disabled for persisted fallback test.")


def test_option_chain_context_summarizes_nearest_persisted_expiry(monkeypatch):
    monkeypatch.setattr(option_chain_context, "_build_finance_data_hub_context", _force_hub_unavailable)
    session = _session()
    repository = OptionRepository(session)
    for option_symbol, strike, option_type, open_interest, gamma in (
        ("SPY260619C00750000", 750.0, "call", 4200, 0.018),
        ("SPY260619P00740000", 740.0, "put", 5800, 0.024),
        ("SPY260626C00760000", 760.0, "call", 9900, 0.055),
    ):
        repository.upsert_contract(
            OptionContractRecord(
                option_symbol=option_symbol,
                underlying_symbol="SPY",
                expiry=date(2026, 6, 19) if "0619" in option_symbol else date(2026, 6, 26),
                strike=strike,
                option_type=option_type,
                exercise_style="american",
                expiration_type="weekly",
                source="finance_data_hub",
            )
        )
        repository.upsert_snapshot(
            OptionSnapshotRecord(
                option_symbol=option_symbol,
                underlying_symbol="SPY",
                timestamp=datetime(2026, 6, 18, 20, 0, tzinfo=UTC),
                bid=4.2,
                ask=4.4,
                last=4.3,
                volume=220,
                open_interest=open_interest,
                implied_volatility=0.19,
                delta=0.42,
                gamma=gamma,
                theta=-0.09,
                vega=0.21,
                source="finance_data_hub",
            )
        )

    context = build_option_chain_context(session, symbol="spy", analysis_date=date(2026, 6, 18))

    assert "最近到期日 2026-06-19" in context
    assert "覆盖 2 个合约" in context
    assert "Open interest 集中合约" in context
    assert "Gamma 敏感合约" in context
    assert "SPY260619P00740000" in context
    assert "SPY260626C00760000" not in context


def test_option_chain_context_returns_empty_when_no_snapshot_exists(monkeypatch):
    monkeypatch.setattr(option_chain_context, "_build_finance_data_hub_context", _force_hub_unavailable)
    assert build_option_chain_context(_session(), symbol="QQQ", analysis_date=date(2026, 6, 18)) == ""
