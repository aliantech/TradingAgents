from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app
from app.market_data.provider_readiness import check_market_data_provider_readiness


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


def test_finance_data_hub_readiness_reports_missing_base_url():
    readiness = check_market_data_provider_readiness(
        Settings(market_data_provider="finance_data_hub", finance_data_hub_base_url="")
    )

    assert readiness.provider == "finance_data_hub"
    assert readiness.ready is False
    assert readiness.missing == ["AQUANTLENS_FINANCE_DATA_HUB_BASE_URL"]


def test_finance_data_hub_readiness_reports_ready():
    readiness = check_market_data_provider_readiness(
        Settings(market_data_provider="finance_data_hub", finance_data_hub_base_url="http://127.0.0.1:18180")
    )

    assert readiness.ready is True
    assert readiness.missing == []


def test_provider_readiness_api_uses_runtime_settings():
    session = _session()
    client = _client_with_session(session)
    try:
        settings_response = client.put(
            "/api/settings",
            json={
                "items": [
                    {
                        "key": "AQUANTLENS_FINANCE_DATA_HUB_BASE_URL",
                        "value": "http://hub.test",
                        "category": "api",
                        "is_secret": False,
                    }
                ]
            },
        )
        response = client.get("/api/market-data/provider-readiness?provider=finance_data_hub")
    finally:
        app.dependency_overrides.clear()

    assert settings_response.status_code == 200
    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "finance_data_hub"
    assert payload["ready"] is True
    assert payload["missing"] == []
