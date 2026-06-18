from fastapi.testclient import TestClient

from app.main import app
from tests.test_strategy_lab_contracts import sample_bars


def test_strategy_lab_saves_lists_gets_and_duplicates_experiments():
    client = TestClient(app)

    preview_response = client.post(
        "/api/strategy-lab/signal-strategy/preview",
        json=preview_payload(),
    )
    assert preview_response.status_code == 200
    preview = preview_response.json()

    create_response = client.post(
        "/api/strategy-lab/experiments",
        json={
            "title": "SPY MA cross baseline",
            "symbol": "SPY",
            "strategy_id": preview["strategy"]["strategy_id"],
            "parameters": preview["strategy"]["parameters"],
            "preview": preview,
            "report_id": None,
        },
    )
    assert create_response.status_code == 201
    experiment = create_response.json()
    assert experiment["title"] == "SPY MA cross baseline"
    assert experiment["symbol"] == "SPY"
    assert experiment["scope"] == "research_only"
    assert experiment["preview"]["backtest"]["final_equity"] == 9997

    list_response = client.get("/api/strategy-lab/experiments?symbol=SPY")
    assert list_response.status_code == 200
    assert list_response.json()["experiments"][0]["experiment_id"] == experiment["experiment_id"]

    get_response = client.get(f"/api/strategy-lab/experiments/{experiment['experiment_id']}")
    assert get_response.status_code == 200
    assert get_response.json()["preview"]["overlay"]["markers"][-1]["shape"] == "arrowDown"

    duplicate_response = client.post(f"/api/strategy-lab/experiments/{experiment['experiment_id']}/duplicate")
    assert duplicate_response.status_code == 201
    duplicate = duplicate_response.json()
    assert duplicate["experiment_id"] != experiment["experiment_id"]
    assert duplicate["title"] == "SPY MA cross baseline Copy"
    assert duplicate["preview"] == experiment["preview"]


def preview_payload():
    return {
        "symbol": "SPY",
        "fast_window": 2,
        "slow_window": 3,
        "initial_equity": 10_000,
        "bars": sample_bars(),
    }
