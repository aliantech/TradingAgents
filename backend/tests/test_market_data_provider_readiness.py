from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.db.base import Base
from app.db.session import get_db_session
from app.main import app
from app.market_data import cli
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


def test_polygon_readiness_reports_missing_key_without_secret_value():
    readiness = check_market_data_provider_readiness(
        Settings(market_data_provider="polygon", polygon_api_key="", polygon_base_url="https://api.polygon.io")
    )

    assert readiness.provider == "polygon"
    assert readiness.ready is False
    assert readiness.missing == ["AQUANTLENS_POLYGON_API_KEY"]
    assert readiness.message == "Polygon provider is missing required runtime configuration."
    assert "apiKey" not in repr(readiness)


def test_polygon_readiness_reports_ready_without_exposing_key():
    readiness = check_market_data_provider_readiness(
        Settings(market_data_provider="polygon", polygon_api_key="secret-value", polygon_base_url="https://api.polygon.io")
    )

    assert readiness.ready is True
    assert readiness.missing == []
    assert readiness.message == "Polygon provider is ready for a live smoke run."
    assert "secret-value" not in repr(readiness)


def test_provider_readiness_api_uses_runtime_settings_without_printing_secret():
    session = _session()
    client = _client_with_session(session)
    try:
        settings_response = client.put(
            "/api/settings",
            json={
                "items": [
                    {
                        "key": "AQUANTLENS_POLYGON_API_KEY",
                        "value": "secret-value",
                        "category": "api",
                        "is_secret": True,
                    }
                ]
            },
        )
        response = client.get("/api/market-data/provider-readiness?provider=polygon")
    finally:
        app.dependency_overrides.clear()

    assert settings_response.status_code == 200
    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "polygon"
    assert payload["ready"] is True
    assert payload["missing"] == []
    assert "secret-value" not in response.text


def test_cli_provider_readiness_exits_nonzero_when_missing_key(monkeypatch, capsys):
    monkeypatch.setattr(cli, "settings", Settings(market_data_provider="polygon", polygon_api_key=""))

    exit_code = cli.main(["provider-readiness", "--provider", "polygon"])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "AQUANTLENS_POLYGON_API_KEY" in output
    assert "apiKey" not in output
