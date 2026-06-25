from collections.abc import Generator
from datetime import UTC, date, datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db_session
from app.main import app
from app.market_data.repository import MarketDataRepository
from app.market_data.schemas import MarketBar
from app.options import router as options_router
from app.options.repository import OptionContractRecord, OptionRepository, OptionSnapshotRecord


def _client_with_session(session: Session) -> TestClient:
    def override_session() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_db_session] = override_session
    return TestClient(app)


def _session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_options_chain_api_reads_persisted_snapshots():
    session = _session()
    repository = OptionRepository(session)
    repository.upsert_contract(
        OptionContractRecord(
            option_symbol="SPY240621C00550000",
            underlying_symbol="SPY",
            expiry=date(2024, 6, 21),
            strike=550.0,
            option_type="call",
            exercise_style="american",
            expiration_type="weekly",
            source="polygon",
        )
    )
    repository.upsert_snapshot(
        OptionSnapshotRecord(
            option_symbol="SPY240621C00550000",
            underlying_symbol="SPY",
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
        )
    )

    client = _client_with_session(session)
    try:
        response = client.get("/api/options/chain?underlying=spy&expiry=2024-06-21")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["underlying_symbol"] == "SPY"
    assert payload["expiry"] == "2024-06-21"
    assert len(payload["snapshots"]) == 1
    assert payload["snapshots"][0]["option_symbol"] == "SPY240621C00550000"
    assert payload["snapshots"][0]["source"] == "polygon"
    assert payload["snapshots"][0]["bid"] == 4.2


def test_options_chain_api_uses_nearest_finance_data_hub_expiry_when_expiry_is_missing(monkeypatch):
    class FakeFinanceDataHubClient:
        def __init__(self, base_url: str) -> None:
            self.base_url = base_url

        def list_option_latest_quote_rows(self, *, underlying_symbol: str, expiry=None):
            assert underlying_symbol == "SPY"
            assert expiry is None
            return [
                {"expiration_date": "2026-06-27"},
                {"expiration_date": "2026-06-25"},
            ]

        def list_option_latest_quotes(self, *, underlying_symbol: str, expiry):
            assert underlying_symbol == "SPY"
            assert expiry == date(2026, 6, 25)
            return [
                OptionSnapshotRecord(
                    option_symbol="O:SPY260625C00726000",
                    underlying_symbol="SPY",
                    timestamp=datetime(2026, 6, 25, 13, 30, tzinfo=UTC),
                    bid=1.1,
                    ask=1.2,
                    last=1.15,
                    volume=10,
                    open_interest=100,
                    implied_volatility=0.2,
                    delta=0.4,
                    gamma=0.01,
                    theta=-0.02,
                    vega=0.03,
                    source="option_quotes_latest",
                )
            ]

    monkeypatch.setattr(options_router, "FinanceDataHubClient", FakeFinanceDataHubClient)
    session = _session()
    client = _client_with_session(session)
    try:
        response = client.get("/api/options/chain?underlying=spy")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["underlying_symbol"] == "SPY"
    assert payload["expiry"] == "2026-06-25"
    assert len(payload["snapshots"]) == 1
    assert payload["snapshots"][0]["option_symbol"] == "O:SPY260625C00726000"


def test_options_chain_api_returns_empty_snapshots_when_no_provider_data():
    session = _session()
    client = _client_with_session(session)
    try:
        response = client.get("/api/options/chain?underlying=spx&expiry=2026-06-17")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["underlying_symbol"] == "SPX"
    assert payload["expiry"] == "2026-06-17"
    assert payload["snapshots"] == []


def test_options_contracts_api_reads_persisted_contracts():
    session = _session()
    repository = OptionRepository(session)
    repository.upsert_contract(
        OptionContractRecord(
            option_symbol="SPY240621P00550000",
            underlying_symbol="SPY",
            expiry=date(2024, 6, 21),
            strike=550.0,
            option_type="put",
            exercise_style="american",
            expiration_type="weekly",
            source="polygon",
        )
    )

    client = _client_with_session(session)
    try:
        response = client.get("/api/options/contracts?underlying=spy&expiry=2024-06-21")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["underlying_symbol"] == "SPY"
    assert payload["expiry"] == "2024-06-21"
    assert payload["contracts"] == [
        {
            "option_symbol": "SPY240621P00550000",
            "underlying_symbol": "SPY",
            "expiry": "2024-06-21",
            "strike": 550.0,
            "option_type": "put",
            "exercise_style": "american",
            "expiration_type": "weekly",
            "source": "polygon",
        }
    ]


def test_options_contracts_api_returns_empty_contracts_when_no_provider_data():
    session = _session()
    client = _client_with_session(session)
    try:
        response = client.get("/api/options/contracts?underlying=spx&expiry=2026-06-17")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["underlying_symbol"] == "SPX"
    assert payload["expiry"] == "2026-06-17"
    assert payload["contracts"] == []


def test_options_bars_api_reads_persisted_option_bars():
    session = _session()
    MarketDataRepository(session).save_bars(
        [
            MarketBar(
                symbol="SPY240621C00550000",
                timeframe="1m",
                timestamp=datetime(2024, 6, 17, 13, 30, tzinfo=UTC),
                open=4.1,
                high=4.4,
                low=4.0,
                close=4.3,
                volume=120,
                source="polygon",
            )
        ],
        asset_type="option",
    )
    client = _client_with_session(session)
    try:
        response = client.get("/api/options/bars?option_symbol=spy240621c00550000&timeframe=1m")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["option_symbol"] == "SPY240621C00550000"
    assert payload["timeframe"] == "1m"
    assert payload["bars"][0]["close"] == 4.3
    assert payload["bars"][0]["source"] == "polygon"


def test_options_bars_api_returns_empty_bars_when_no_provider_data():
    session = _session()
    client = _client_with_session(session)
    try:
        response = client.get("/api/options/bars?option_symbol=SPXW260617C05900000&timeframe=5m")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["option_symbol"] == "SPXW260617C05900000"
    assert payload["timeframe"] == "5m"
    assert payload["bars"] == []
