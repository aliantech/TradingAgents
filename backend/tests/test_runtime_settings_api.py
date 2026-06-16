from fastapi.testclient import TestClient

from app.main import app
from app.runtime_config import runtime_config


def test_runtime_settings_api_updates_polygon_key_without_returning_secret():
    runtime_config.clear()
    client = TestClient(app)

    response = client.put(
        "/api/settings/provider",
        json={
            "provider": "polygon",
            "polygon_api_key": "test-secret-key",
            "polygon_base_url": "https://api.massive.test",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "polygon"
    assert payload["polygon_configured"] is True
    assert payload["polygon_base_url"] == "https://api.massive.test"
    assert "test-secret-key" not in response.text


def test_runtime_settings_make_polygon_readiness_ready_without_env_key():
    runtime_config.clear()
    client = TestClient(app)

    before = client.get("/api/market-data/provider-readiness?provider=polygon").json()
    client.put(
        "/api/settings/provider",
        json={
            "provider": "polygon",
            "polygon_api_key": "runtime-secret",
        },
    )
    after = client.get("/api/market-data/provider-readiness?provider=polygon").json()

    assert before["ready"] is False
    assert after["ready"] is True
    assert after["missing"] == []
    assert "runtime-secret" not in str(after)


def test_runtime_settings_rejects_unsupported_provider():
    runtime_config.clear()
    client = TestClient(app)

    response = client.put(
        "/api/settings/provider",
        json={
            "provider": "other",
            "polygon_api_key": "test-secret-key",
        },
    )

    assert response.status_code == 400
    assert "test-secret-key" not in response.text
