from datetime import UTC, date, datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db_session
from app.main import app
from app.market_data.sync_repository import ProviderSyncRepository
from app.options import router
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
                    option_symbol="O:SPX240621C05500000",
                    underlying_symbol=underlying_symbol,
                    expiry=expiry,
                    strike=5500.0,
                    option_type="call",
                    exercise_style="european",
                    expiration_type="weekly",
                    source="polygon",
                ),
                snapshot=OptionSnapshotRecord(
                    option_symbol="O:SPX240621C05500000",
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
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_options_sync_chain_api_persists_chain_and_records_audit(monkeypatch):
    session = _session()

    def override_session():
        yield session

    monkeypatch.setattr(router, "create_options_provider", lambda provider_name, session: FakeOptionChainProvider())
    app.dependency_overrides[get_db_session] = override_session
    try:
        response = TestClient(app).post(
            "/api/options/sync-chain",
            json={"underlying_symbol": "spx", "expiry": "2024-06-21", "provider": "polygon", "limit": 25},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 202
    payload = response.json()
    assert payload["status"] == "succeeded"
    assert payload["rows_written"] == 1
    assert payload["underlying_symbol"] == "SPX"
    snapshots = OptionRepository(session).list_chain_snapshots(
        underlying_symbol="SPX",
        expiry=date(2024, 6, 21),
    )
    assert len(snapshots) == 1
    assert snapshots[0].source == "polygon"
    runs = ProviderSyncRepository(session).list_runs(provider="polygon", sync_type="options_chain")
    assert len(runs) == 1


def test_options_sync_chain_api_rejects_when_disabled(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(
        router,
        "resolve_runtime_settings",
        lambda session: settings.model_copy(update={"manual_market_sync_enabled": False}),
    )

    response = TestClient(app).post(
        "/api/options/sync-chain",
        json={"underlying_symbol": "SPX", "expiry": "2024-06-21", "provider": "polygon"},
    )

    assert response.status_code == 403
