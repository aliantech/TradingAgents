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


def test_strategy_lab_compares_saved_experiments():
    client = TestClient(app)

    baseline = create_experiment(client, "SPY MA baseline", preview_payload(fast_window=2, slow_window=3))
    candidate = create_experiment(client, "SPY MA flat", preview_payload(fast_window=5, slow_window=5))

    compare_response = client.get(
        "/api/strategy-lab/experiments/compare",
        params={
            "base_id": baseline["experiment_id"],
            "candidate_id": candidate["experiment_id"],
        },
    )

    assert compare_response.status_code == 200
    comparison = compare_response.json()
    assert comparison["scope"] == "research_only"
    assert comparison["symbol"] == "SPY"
    assert comparison["base"]["title"] == "SPY MA baseline"
    assert comparison["candidate"]["title"] == "SPY MA flat"
    assert comparison["deltas"]["final_equity"] == 3
    assert comparison["deltas"]["trade_count"] == -1
    assert comparison["deltas"]["marker_count"] == -2
    assert comparison["parameter_deltas"]["fast_window"] == {"base": 2, "candidate": 5, "changed": True}
    assert comparison["parameter_deltas"]["slow_window"] == {"base": 3, "candidate": 5, "changed": True}


def test_strategy_lab_curates_experiments_with_tags_notes_and_archive():
    client = TestClient(app)

    experiment = create_experiment(
        client,
        "SPY MA candidate",
        preview_payload(),
        tags=["breakout", "watchlist"],
        notes="Candidate for further research review.",
    )

    assert experiment["tags"] == ["breakout", "watchlist"]
    assert experiment["notes"] == "Candidate for further research review."
    assert experiment["archived"] is False

    tag_response = client.get("/api/strategy-lab/experiments", params={"symbol": "SPY", "tag": "breakout"})
    assert tag_response.status_code == 200
    assert [row["experiment_id"] for row in tag_response.json()["experiments"]] == [experiment["experiment_id"]]

    update_response = client.patch(
        f"/api/strategy-lab/experiments/{experiment['experiment_id']}",
        json={
            "tags": ["reviewed"],
            "notes": "Archived after comparison.",
            "archived": True,
        },
    )
    assert update_response.status_code == 200
    archived = update_response.json()
    assert archived["tags"] == ["reviewed"]
    assert archived["notes"] == "Archived after comparison."
    assert archived["archived"] is True

    default_list_response = client.get("/api/strategy-lab/experiments", params={"symbol": "SPY"})
    assert default_list_response.status_code == 200
    assert archived["experiment_id"] not in [
        row["experiment_id"] for row in default_list_response.json()["experiments"]
    ]

    archived_list_response = client.get(
        "/api/strategy-lab/experiments",
        params={"symbol": "SPY", "include_archived": "true"},
    )
    assert archived_list_response.status_code == 200
    assert archived["experiment_id"] in [
        row["experiment_id"] for row in archived_list_response.json()["experiments"]
    ]

    duplicate_response = client.post(f"/api/strategy-lab/experiments/{archived['experiment_id']}/duplicate")
    assert duplicate_response.status_code == 201
    duplicate = duplicate_response.json()
    assert duplicate["experiment_id"] != archived["experiment_id"]
    assert duplicate["tags"] == ["reviewed"]
    assert duplicate["notes"] == "Archived after comparison."
    assert duplicate["archived"] is False


def test_strategy_lab_promotes_experiments_with_review_gate():
    client = TestClient(app)

    experiment = create_experiment(client, "SPY MA review candidate", preview_payload())

    assert experiment["review_status"] == "draft"
    assert experiment["review_checklist"] == {}

    update_response = client.patch(
        f"/api/strategy-lab/experiments/{experiment['experiment_id']}",
        json={
            "review_status": "candidate",
            "review_checklist": {
                "data_range_reviewed": True,
                "parameters_reviewed": True,
                "backtest_reviewed": True,
                "risk_notes_added": True,
                "human_reviewed": True,
            },
        },
    )
    assert update_response.status_code == 200
    candidate = update_response.json()
    assert candidate["review_status"] == "candidate"
    assert candidate["review_checklist"]["human_reviewed"] is True

    candidate_list_response = client.get(
        "/api/strategy-lab/experiments",
        params={"symbol": "SPY", "review_status": "candidate"},
    )
    assert candidate_list_response.status_code == 200
    assert [row["experiment_id"] for row in candidate_list_response.json()["experiments"]] == [
        candidate["experiment_id"]
    ]

    rejected_list_response = client.get(
        "/api/strategy-lab/experiments",
        params={"symbol": "SPY", "review_status": "rejected"},
    )
    assert rejected_list_response.status_code == 200
    assert candidate["experiment_id"] not in [
        row["experiment_id"] for row in rejected_list_response.json()["experiments"]
    ]


def test_strategy_lab_lists_candidate_review_board():
    client = TestClient(app)

    baseline = create_experiment(
        client,
        "SPY MA candidate baseline",
        preview_payload(fast_window=2, slow_window=3),
        tags=["breakout"],
    )
    stronger = create_experiment(
        client,
        "SPY MA candidate flat",
        preview_payload(fast_window=5, slow_window=5),
        tags=["breakout", "watchlist"],
    )
    rejected = create_experiment(client, "SPY MA rejected", preview_payload(), tags=["breakout"])
    archived = create_experiment(client, "SPY MA archived candidate", preview_payload(), tags=["breakout"])

    for experiment in [baseline, stronger, archived]:
        response = client.patch(
            f"/api/strategy-lab/experiments/{experiment['experiment_id']}",
            json={"review_status": "candidate", "review_checklist": {"human_reviewed": True}},
        )
        assert response.status_code == 200
    rejected_response = client.patch(
        f"/api/strategy-lab/experiments/{rejected['experiment_id']}",
        json={"review_status": "rejected"},
    )
    assert rejected_response.status_code == 200
    archived_response = client.patch(
        f"/api/strategy-lab/experiments/{archived['experiment_id']}",
        json={"archived": True},
    )
    assert archived_response.status_code == 200

    board_response = client.get(
        "/api/strategy-lab/experiments/candidates",
        params={"symbol": "SPY", "tag": "breakout", "sort_by": "return_pct", "sort_order": "desc"},
    )
    assert board_response.status_code == 200
    board = board_response.json()
    assert board["scope"] == "research_only"
    assert [row["experiment_id"] for row in board["candidates"]] == [
        stronger["experiment_id"],
        baseline["experiment_id"],
    ]
    assert board["candidates"][0]["return_pct"] >= board["candidates"][1]["return_pct"]
    assert board["candidates"][0]["trade_count"] == 0
    assert board["candidates"][0]["tags"] == ["breakout", "watchlist"]


def preview_payload(fast_window: int = 2, slow_window: int = 3):
    return {
        "symbol": "SPY",
        "fast_window": fast_window,
        "slow_window": slow_window,
        "initial_equity": 10_000,
        "bars": sample_bars(),
    }


def create_experiment(
    client: TestClient,
    title: str,
    payload: dict,
    tags: list[str] | None = None,
    notes: str | None = None,
):
    preview_response = client.post(
        "/api/strategy-lab/signal-strategy/preview",
        json=payload,
    )
    assert preview_response.status_code == 200
    preview = preview_response.json()
    request_json = {
        "title": title,
        "symbol": payload["symbol"],
        "strategy_id": preview["strategy"]["strategy_id"],
        "parameters": preview["strategy"]["parameters"],
        "preview": preview,
        "report_id": None,
    }
    if tags is not None:
        request_json["tags"] = tags
    if notes is not None:
        request_json["notes"] = notes
    create_response = client.post("/api/strategy-lab/experiments", json=request_json)
    assert create_response.status_code == 201
    return create_response.json()
