from fastapi.testclient import TestClient

from app.main import app
from tests.test_strategy_lab_contracts import sample_bars


def test_strategy_lab_preview_api_returns_live_research_payload():
    client = TestClient(app)

    response = client.post(
        "/api/strategy-lab/signal-strategy/preview",
        json={
            "symbol": "SPY",
            "fast_window": 2,
            "slow_window": 3,
            "initial_equity": 10_000,
            "bars": sample_bars(),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["scope"] == "research_only"
    assert body["strategy"]["parameters"] == {"fast_window": 2, "slow_window": 3}
    assert body["signals"][-1]["signal"] == -1
    assert body["backtest"]["final_equity"] == 9997
    assert body["overlay"]["markers"][-1]["shape"] == "arrowDown"
    assert body["note"] is None
