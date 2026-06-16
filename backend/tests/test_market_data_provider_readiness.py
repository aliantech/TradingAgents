from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app
from app.market_data import cli, router
from app.market_data.provider_readiness import check_market_data_provider_readiness


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


def test_provider_readiness_api_uses_runtime_settings_without_printing_secret(monkeypatch):
    monkeypatch.setattr(router, "settings", Settings(market_data_provider="polygon", polygon_api_key="secret-value"))

    response = TestClient(app).get("/api/market-data/provider-readiness?provider=polygon")

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
