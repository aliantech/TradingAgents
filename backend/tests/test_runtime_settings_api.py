from fastapi.testclient import TestClient

from app.main import app
from app.runtime_config import runtime_config


def test_runtime_settings_api_updates_finance_data_hub_base_url():
    runtime_config.clear()
    client = TestClient(app)

    response = client.put(
        "/api/settings/provider",
        json={
            "provider": "finance_data_hub",
            "finance_data_hub_base_url": "http://hub.test",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "finance_data_hub"
    assert payload["finance_data_hub_base_url"] == "http://hub.test"


def test_runtime_settings_rejects_unsupported_provider():
    runtime_config.clear()
    client = TestClient(app)

    response = client.put(
        "/api/settings/provider",
        json={
            "provider": "other",
            "finance_data_hub_base_url": "http://hub.test",
        },
    )

    assert response.status_code == 400
