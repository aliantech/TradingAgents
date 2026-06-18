from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db_session
from app.main import app


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


def test_settings_api_persists_values_and_masks_secret_reads():
    session = _session()
    client = _client_with_session(session)
    try:
        response = client.put(
            "/api/settings",
            json={
                "items": [
                    {
                        "key": "AQUANTLENS_POLYGON_BASE_URL",
                        "value": "https://api.polygon.io",
                        "category": "api",
                        "is_secret": False,
                    },
                    {
                        "key": "AQUANTLENS_POLYGON_API_KEY",
                        "value": "secret-value",
                        "category": "api",
                        "is_secret": True,
                    },
                ]
            },
        )
        assert response.status_code == 200

        payload = client.get("/api/settings").json()
        readiness = client.get("/api/market-data/provider-readiness?provider=polygon").json()
    finally:
        app.dependency_overrides.clear()

    settings_by_key = {item["key"]: item for item in payload["items"]}
    assert settings_by_key["AQUANTLENS_POLYGON_BASE_URL"]["value"] == "https://api.polygon.io"
    assert settings_by_key["AQUANTLENS_POLYGON_API_KEY"]["value"] is None
    assert settings_by_key["AQUANTLENS_POLYGON_API_KEY"]["has_value"] is True
    assert "secret-value" not in str(payload)
    assert readiness["ready"] is True
    assert readiness["missing"] == []
