from datetime import datetime
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.db.models import (
    PaperAccountModel,
    PaperAuditEventModel,
    PaperFillModel,
    PaperOrderIntentModel,
    PaperPositionModel,
    PaperRiskDecisionModel,
    StrategyExperimentModel,
)
from app.db.session import SessionLocal, initialize_database
from app.main import app
from app.paper_trading.contracts import PaperAccount, PaperAccountStatus
from app.paper_trading.repository import PaperTradingRepository


@pytest.fixture(autouse=True)
def clean_paper_api_rows():
    initialize_database()
    cleanup_paper_api_rows()
    yield
    cleanup_paper_api_rows()


def test_paper_intent_api_creates_lists_and_reads_draft_intent():
    client = TestClient(app)
    account_id = seed_account()
    candidate_id = seed_candidate_experiment()

    create_response = client.post(
        "/api/paper-trading/intents",
        headers={"Idempotency-Key": "paper-intent-create-1"},
        json={
            "account_id": str(account_id),
            "source_reference_id": str(candidate_id),
            "symbol": "SPY",
            "asset_class": "etf",
            "side": "buy",
            "quantity": 2,
            "order_type": "market",
            "time_in_force": "day",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["scope"] == "paper_only"
    assert created["intent"]["account_id"] == str(account_id)
    assert created["intent"]["symbol"] == "SPY"
    assert created["intent"]["status"] == "draft"
    assert created["latest_risk_decision"] is None
    assert created["audit_events"][-1]["reason_code"] == "intent_created"

    list_response = client.get("/api/paper-trading/intents", params={"account_id": str(account_id)})
    assert list_response.status_code == 200
    assert [row["intent_id"] for row in list_response.json()["intents"]] == [created["intent"]["intent_id"]]

    detail_response = client.get(f"/api/paper-trading/intents/{created['intent']['intent_id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["intent"] == created["intent"]


def test_paper_intent_create_requires_idempotency_key():
    client = TestClient(app)
    account_id = seed_account()
    candidate_id = seed_candidate_experiment()

    response = client.post(
        "/api/paper-trading/intents",
        json={
            "account_id": str(account_id),
            "source_reference_id": str(candidate_id),
            "symbol": "SPY",
            "asset_class": "etf",
            "side": "buy",
            "quantity": 1,
            "order_type": "market",
            "time_in_force": "day",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Idempotency-Key header is required"


def test_paper_intent_create_replays_idempotency_key():
    client = TestClient(app)
    account_id = seed_account()
    candidate_id = seed_candidate_experiment()
    payload = {
        "account_id": str(account_id),
        "source_reference_id": str(candidate_id),
        "symbol": "SPY",
        "asset_class": "etf",
        "side": "buy",
        "quantity": 1,
        "order_type": "market",
        "time_in_force": "day",
    }

    first = client.post(
        "/api/paper-trading/intents",
        headers={"Idempotency-Key": "paper-intent-replay-1"},
        json=payload,
    )
    second = client.post(
        "/api/paper-trading/intents",
        headers={"Idempotency-Key": "paper-intent-replay-1"},
        json=payload,
    )

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["intent"]["intent_id"] == first.json()["intent"]["intent_id"]
    assert second.json()["replayed"] is True


def test_paper_intent_api_runs_riskguard_and_sets_review_status():
    client = TestClient(app)
    account_id = seed_account()
    candidate_id = seed_candidate_experiment()
    intent_id = create_intent(client, account_id, candidate_id)

    response = client.post(
        f"/api/paper-trading/intents/{intent_id}/risk-check",
        json={
            "allowed_symbols": ["SPY"],
            "allowed_asset_classes": ["etf"],
            "max_notional_per_intent": 2_000,
            "max_daily_notional": 5_000,
            "current_daily_notional": 0,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["intent"]["status"] == "awaiting_review"
    assert body["latest_risk_decision"]["result"] == "pass"
    assert body["latest_risk_decision"]["reason_codes"] == ["risk_checks_passed"]
    assert body["audit_events"][-1]["reason_code"] == "risk_checks_passed"


def test_paper_intent_api_records_risk_rejection():
    client = TestClient(app)
    account_id = seed_account()
    candidate_id = seed_candidate_experiment()
    intent_id = create_intent(client, account_id, candidate_id)

    response = client.post(
        f"/api/paper-trading/intents/{intent_id}/risk-check",
        json={
            "allowed_symbols": ["QQQ"],
            "allowed_asset_classes": ["etf"],
            "max_notional_per_intent": 2_000,
            "max_daily_notional": 5_000,
            "current_daily_notional": 0,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["intent"]["status"] == "risk_rejected"
    assert body["latest_risk_decision"]["result"] == "reject"
    assert body["latest_risk_decision"]["reason_codes"] == ["symbol_not_allowlisted"]


def test_paper_intent_api_requires_risk_pass_before_approval():
    client = TestClient(app)
    account_id = seed_account()
    candidate_id = seed_candidate_experiment()
    intent_id = create_intent(client, account_id, candidate_id)

    response = client.post(
        f"/api/paper-trading/intents/{intent_id}/review",
        json={"decision": "approve", "message": "Looks good for paper review."},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "intent must pass RiskGuard before approval"


def test_paper_intent_api_approves_and_rejects_after_review():
    client = TestClient(app)
    account_id = seed_account()
    candidate_id = seed_candidate_experiment()
    approved_intent_id = create_intent(client, account_id, candidate_id, key="approve-flow")
    rejected_intent_id = create_intent(client, account_id, candidate_id, key="reject-flow")

    run_passing_risk_check(client, approved_intent_id)
    approve_response = client.post(
        f"/api/paper-trading/intents/{approved_intent_id}/review",
        json={"decision": "approve", "message": "Approved for paper simulation."},
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["intent"]["status"] == "approved_for_paper"
    assert approve_response.json()["audit_events"][-1]["reason_code"] == "human_approved"

    run_passing_risk_check(client, rejected_intent_id)
    reject_response = client.post(
        f"/api/paper-trading/intents/{rejected_intent_id}/review",
        json={"decision": "reject", "message": "Rejecting this paper idea."},
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["intent"]["status"] == "risk_rejected"
    assert reject_response.json()["audit_events"][-1]["reason_code"] == "human_rejected"


def test_paper_intent_api_submits_approved_intent_to_local_simulation():
    client = TestClient(app)
    account_id = seed_account()
    candidate_id = seed_candidate_experiment()
    intent_id = create_intent(client, account_id, candidate_id, key="submit-flow")
    run_passing_risk_check(client, intent_id)
    approve_response = client.post(
        f"/api/paper-trading/intents/{intent_id}/review",
        json={"decision": "approve", "message": "Approved for paper simulation."},
    )
    assert approve_response.status_code == 200

    submit_response = client.post(
        f"/api/paper-trading/intents/{intent_id}/paper-submit",
        json={"market_price": 500},
    )

    assert submit_response.status_code == 200
    body = submit_response.json()
    assert body["intent"]["status"] == "paper_filled"
    assert body["latest_risk_decision"]["result"] == "pass"
    assert body["audit_events"][-1]["reason_code"] == "paper_filled"

    session = SessionLocal()
    try:
        repository = PaperTradingRepository(session)
        account = repository.get_account(account_id)
        fills = repository.list_fills_for_intent(UUID(intent_id))
        positions = repository.list_positions_for_account(account_id)
        assert account.current_cash == 99_000
        assert len(fills) == 1
        assert fills[0].fill_price == 500
        assert positions[0].quantity == 2
        assert positions[0].average_price == 500
    finally:
        session.close()


def test_paper_intent_api_rejects_submit_before_approval():
    client = TestClient(app)
    account_id = seed_account()
    candidate_id = seed_candidate_experiment()
    intent_id = create_intent(client, account_id, candidate_id, key="submit-before-approval")

    submit_response = client.post(
        f"/api/paper-trading/intents/{intent_id}/paper-submit",
        json={"market_price": 500},
    )

    assert submit_response.status_code == 409
    assert submit_response.json()["detail"] == "intent_not_approved_for_paper"


def test_paper_intent_api_cancels_unfilled_intent():
    client = TestClient(app)
    account_id = seed_account()
    candidate_id = seed_candidate_experiment()
    intent_id = create_intent(client, account_id, candidate_id, key="cancel-flow")

    cancel_response = client.post(
        f"/api/paper-trading/intents/{intent_id}/cancel",
        json={"message": "Cancelling paper draft."},
    )

    assert cancel_response.status_code == 200
    body = cancel_response.json()
    assert body["intent"]["status"] == "paper_cancelled"
    assert body["audit_events"][-1]["reason_code"] == "paper_cancelled"


def test_paper_intent_api_rejects_cancel_after_fill():
    client = TestClient(app)
    account_id = seed_account()
    candidate_id = seed_candidate_experiment()
    intent_id = create_intent(client, account_id, candidate_id, key="cancel-after-fill")
    run_passing_risk_check(client, intent_id)
    approve_response = client.post(
        f"/api/paper-trading/intents/{intent_id}/review",
        json={"decision": "approve", "message": "Approved for paper simulation."},
    )
    assert approve_response.status_code == 200
    submit_response = client.post(
        f"/api/paper-trading/intents/{intent_id}/paper-submit",
        json={"market_price": 500},
    )
    assert submit_response.status_code == 200

    cancel_response = client.post(
        f"/api/paper-trading/intents/{intent_id}/cancel",
        json={"message": "Too late."},
    )

    assert cancel_response.status_code == 409
    assert cancel_response.json()["detail"] == "intent_cannot_be_cancelled"


def test_paper_intent_api_does_not_expose_broker_or_live_fields():
    client = TestClient(app)
    account_id = seed_account()
    candidate_id = seed_candidate_experiment()
    intent_id = create_intent(client, account_id, candidate_id)

    response = client.get(f"/api/paper-trading/intents/{intent_id}")

    text = response.text.lower()
    assert "broker" not in text
    assert "live" not in text
    assert "order_id" not in text


def seed_account():
    initialize_database()
    session = SessionLocal()
    try:
        account = PaperAccount(
            account_id=uuid4(),
            name="API paper account",
            base_currency="USD",
            starting_cash=100_000,
            current_cash=100_000,
            status=PaperAccountStatus.ACTIVE,
            created_at=timestamp(),
        )
        PaperTradingRepository(session).save_account(account)
        return account.account_id
    finally:
        session.close()


def seed_candidate_experiment():
    initialize_database()
    session = SessionLocal()
    try:
        experiment = StrategyExperimentModel(
            title="SPY paper candidate",
            symbol="SPY",
            strategy_id="ma-cross-research",
            scope="research_only",
            parameters={"fast_window": 2, "slow_window": 3},
            preview_json={"backtest": {"return_pct": 1.2}},
            review_status="candidate",
        )
        session.add(experiment)
        session.commit()
        session.refresh(experiment)
        return experiment.id
    finally:
        session.close()


def create_intent(client, account_id, candidate_id, key="paper-api-intent"):
    response = client.post(
        "/api/paper-trading/intents",
        headers={"Idempotency-Key": key},
        json={
            "account_id": str(account_id),
            "source_reference_id": str(candidate_id),
            "symbol": "SPY",
            "asset_class": "etf",
            "side": "buy",
            "quantity": 2,
            "order_type": "market",
            "time_in_force": "day",
        },
    )
    assert response.status_code in {200, 201}
    return response.json()["intent"]["intent_id"]


def run_passing_risk_check(client, intent_id):
    response = client.post(
        f"/api/paper-trading/intents/{intent_id}/risk-check",
        json={
            "allowed_symbols": ["SPY"],
            "allowed_asset_classes": ["etf"],
            "max_notional_per_intent": 2_000,
            "max_daily_notional": 5_000,
            "current_daily_notional": 0,
        },
    )
    assert response.status_code == 200


def timestamp():
    return datetime(2026, 6, 20, 13, 30)


def cleanup_paper_api_rows():
    session = SessionLocal()
    try:
        for model in (
            PaperAuditEventModel,
            PaperRiskDecisionModel,
            PaperFillModel,
            PaperPositionModel,
            PaperOrderIntentModel,
            PaperAccountModel,
        ):
            session.execute(delete(model))
        session.execute(
            delete(StrategyExperimentModel)
            .where(StrategyExperimentModel.title == "SPY paper candidate")
            .where(StrategyExperimentModel.strategy_id == "ma-cross-research")
        )
        session.commit()
    finally:
        session.close()
