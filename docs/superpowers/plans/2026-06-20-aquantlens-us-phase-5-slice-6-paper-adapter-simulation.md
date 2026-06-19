# AQuantLens US Phase 5 Slice 6 Paper Adapter and Position Simulation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic local paper adapter that turns approved paper intents into simulated fills, cash movements, position updates, and cancellable non-filled intents without adding broker integration, live execution, network calls, or agent-facing trading tools.

**Architecture:** Add a focused `app.paper_trading.adapter` module for pure paper execution rules and keep persistence in `PaperTradingRepository`. Extend the human-facing paper trading router with explicit paper-only submit and cancel endpoints. The adapter never imports broker SDKs, never performs network I/O, and only accepts caller-supplied deterministic prices.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy ORM, pytest, FastAPI `TestClient`, existing paper trading contracts/repository/router/RiskGuard.

---

## Scope

This plan implements Phase 5 Slice 6 only.

Included:

- Local deterministic paper adapter.
- Paper fill creation for approved paper intents.
- Paper cash updates for buys and sells.
- Paper position creation and update.
- Rejection paths for insufficient cash and insufficient position.
- Cancel flow for paper intents that have not filled.
- Human-facing API endpoints for paper submit and cancel.
- Audit events for simulated fills, rejected paper execution, and cancellations.
- Focused adapter and API tests.
- Safety grep checks.
- Roadmap and project status updates.

Excluded:

- Broker integration.
- Live execution.
- Broker credentials or broker account identifiers.
- Network calls.
- Market data fetching inside the adapter.
- Agent Gateway write scope.
- MCP trading tools.
- Short selling.
- Partial fills.
- Slippage model.
- Commissions and fees.
- Frontend UI.

## Behavioral Rules

Execution:

- Only intents with status `approved_for_paper` can be submitted to the paper adapter.
- A successful paper submit creates exactly one `PaperFill`.
- A successful paper submit updates the intent to `paper_filled`.
- Market orders use the request `market_price`.
- Limit orders use `limit_price`.
- Buy notional is `quantity * fill_price * multiplier`.
- Sell notional is `quantity * fill_price * multiplier`.
- Options use multiplier `100`; equities and ETFs use multiplier `1`.
- Buy requires enough `PaperAccount.current_cash`.
- Sell requires an existing long position with `quantity >= intent.quantity`.
- No short selling in Slice 6.

Position math:

- New buy position quantity is existing quantity plus fill quantity.
- New buy average price is weighted by quantity, not notional multiplier.
- Sell position quantity is existing quantity minus fill quantity.
- Sell keeps average price unchanged when remaining quantity is positive.
- Sell resets average price to `0` when remaining quantity is `0`.

Cancellation:

- Cancel is allowed for `draft`, `awaiting_review`, and `approved_for_paper`.
- Cancel is rejected for `risk_rejected`, `paper_filled`, and `paper_cancelled`.
- Cancel updates status to `paper_cancelled`.
- Cancel creates an audit event with reason code `paper_cancelled`.

API:

- Add `POST /api/paper-trading/intents/{intent_id}/paper-submit`.
- Add `POST /api/paper-trading/intents/{intent_id}/cancel`.
- Submit request accepts deterministic `market_price`.
- Submit response reuses `PaperIntentResponse` and adds persisted fill/position/cash effects in the database.
- Do not expose broker, live, external order id, account number, or network fields.

## File Structure

- Create `backend/app/paper_trading/adapter.py`
  - Pure local paper simulation rules.
- Modify `backend/app/paper_trading/repository.py`
  - Add account cash update and position lookup helpers.
- Modify `backend/app/paper_trading/router.py`
  - Add submit/cancel request schemas and endpoints.
- Create `backend/tests/test_paper_trading_adapter.py`
  - Unit tests for adapter cash, position, rejection, cancellation, and safety.
- Modify `backend/tests/test_paper_trading_api.py`
  - API tests for submit and cancel endpoints.
- Modify `docs/roadmap/phase-5-roadmap.md`
  - Mark Slice 6 implemented after verification.
- Modify `PROJECT.md`
  - Update current Phase 5 state after verification.

## Task 1: Add Failing Paper Adapter Tests

**Files:**
- Create: `backend/tests/test_paper_trading_adapter.py`

- [ ] **Step 1: Write the failing adapter test file**

Create `backend/tests/test_paper_trading_adapter.py` with this content:

```python
from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.paper_trading.adapter import (
    PaperExecutionError,
    cancel_paper_intent,
    execute_paper_intent,
)
from app.paper_trading.contracts import (
    AssetClass,
    OrderIntentStatus,
    OrderSide,
    OrderSource,
    OrderType,
    PaperAccount,
    PaperAccountStatus,
    PaperOrderIntent,
    PaperPosition,
    TimeInForce,
)
from app.paper_trading.repository import PaperTradingRepository


def test_paper_adapter_buys_and_updates_cash_position_fill_and_status():
    repository, account = repository_with_account()
    intent = paper_intent(account.account_id, side=OrderSide.BUY, quantity=2)
    repository.save_order_intent(intent)

    result = execute_paper_intent(repository, intent.intent_id, market_price=500, filled_at=timestamp())

    assert result.fill.fill_price == 500
    assert result.fill.quantity == 2
    assert result.account.current_cash == 99_000
    assert result.position.quantity == 2
    assert result.position.average_price == 500
    assert result.intent.status == OrderIntentStatus.PAPER_FILLED
    assert repository.list_fills_for_intent(intent.intent_id) == [result.fill]
    assert repository.list_audit_events(intent.intent_id)[-1].reason_code == "paper_filled"


def test_paper_adapter_buys_existing_position_with_weighted_average():
    repository, account = repository_with_account()
    repository.save_position(
        PaperPosition(
            position_id=uuid4(),
            account_id=account.account_id,
            symbol="SPY",
            asset_class=AssetClass.ETF,
            quantity=2,
            average_price=400,
            updated_at=timestamp(),
        )
    )
    intent = paper_intent(account.account_id, side=OrderSide.BUY, quantity=2)
    repository.save_order_intent(intent)

    result = execute_paper_intent(repository, intent.intent_id, market_price=600, filled_at=timestamp())

    assert result.account.current_cash == 98_800
    assert result.position.quantity == 4
    assert result.position.average_price == 500


def test_paper_adapter_sells_existing_position_and_updates_cash():
    repository, account = repository_with_account()
    repository.save_position(
        PaperPosition(
            position_id=uuid4(),
            account_id=account.account_id,
            symbol="SPY",
            asset_class=AssetClass.ETF,
            quantity=3,
            average_price=450,
            updated_at=timestamp(),
        )
    )
    intent = paper_intent(account.account_id, side=OrderSide.SELL, quantity=1)
    repository.save_order_intent(intent)

    result = execute_paper_intent(repository, intent.intent_id, market_price=500, filled_at=timestamp())

    assert result.account.current_cash == 100_500
    assert result.position.quantity == 2
    assert result.position.average_price == 450
    assert result.intent.status == OrderIntentStatus.PAPER_FILLED


def test_paper_adapter_rejects_buy_when_cash_is_insufficient():
    repository, account = repository_with_account(current_cash=100)
    intent = paper_intent(account.account_id, side=OrderSide.BUY, quantity=1)
    repository.save_order_intent(intent)

    with pytest.raises(PaperExecutionError, match="insufficient_cash"):
        execute_paper_intent(repository, intent.intent_id, market_price=500, filled_at=timestamp())

    assert repository.get_account(account.account_id).current_cash == 100
    assert repository.get_order_intent(intent.intent_id).status == OrderIntentStatus.APPROVED_FOR_PAPER
    assert repository.list_fills_for_intent(intent.intent_id) == []
    assert repository.list_audit_events(intent.intent_id)[-1].reason_code == "insufficient_cash"


def test_paper_adapter_rejects_sell_without_enough_position():
    repository, account = repository_with_account()
    intent = paper_intent(account.account_id, side=OrderSide.SELL, quantity=1)
    repository.save_order_intent(intent)

    with pytest.raises(PaperExecutionError, match="insufficient_position"):
        execute_paper_intent(repository, intent.intent_id, market_price=500, filled_at=timestamp())

    assert repository.get_account(account.account_id).current_cash == 100_000
    assert repository.list_fills_for_intent(intent.intent_id) == []
    assert repository.list_audit_events(intent.intent_id)[-1].reason_code == "insufficient_position"


def test_paper_adapter_rejects_intent_that_is_not_approved_for_paper():
    repository, account = repository_with_account()
    intent = paper_intent(account.account_id, status=OrderIntentStatus.AWAITING_REVIEW)
    repository.save_order_intent(intent)

    with pytest.raises(PaperExecutionError, match="intent_not_approved_for_paper"):
        execute_paper_intent(repository, intent.intent_id, market_price=500, filled_at=timestamp())

    assert repository.list_fills_for_intent(intent.intent_id) == []


def test_paper_adapter_cancels_unfilled_intent():
    repository, account = repository_with_account()
    intent = paper_intent(account.account_id, status=OrderIntentStatus.APPROVED_FOR_PAPER)
    repository.save_order_intent(intent)

    result = cancel_paper_intent(repository, intent.intent_id, message="Human cancelled paper intent.")

    assert result.intent.status == OrderIntentStatus.PAPER_CANCELLED
    assert repository.list_audit_events(intent.intent_id)[-1].reason_code == "paper_cancelled"


def test_paper_adapter_rejects_cancel_after_fill():
    repository, account = repository_with_account()
    intent = paper_intent(account.account_id, status=OrderIntentStatus.PAPER_FILLED)
    repository.save_order_intent(intent)

    with pytest.raises(PaperExecutionError, match="intent_cannot_be_cancelled"):
        cancel_paper_intent(repository, intent.intent_id, message="Too late.")


def test_paper_adapter_does_not_use_broker_network_or_live_execution_fields():
    import app.paper_trading.adapter as adapter

    public_names = " ".join(name.lower() for name in dir(adapter))
    assert "broker" not in public_names
    assert "live" not in public_names
    assert "requests" not in public_names
    assert "httpx" not in public_names
    assert "aiohttp" not in public_names


def repository_with_account(current_cash=100_000):
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    repository = PaperTradingRepository(session)
    account = PaperAccount(
        account_id=uuid4(),
        name="Simulation account",
        base_currency="USD",
        starting_cash=100_000,
        current_cash=current_cash,
        status=PaperAccountStatus.ACTIVE,
        created_at=timestamp(),
    )
    repository.save_account(account)
    return repository, account


def paper_intent(
    account_id,
    *,
    side=OrderSide.BUY,
    quantity=1,
    status=OrderIntentStatus.APPROVED_FOR_PAPER,
    order_type=OrderType.MARKET,
    limit_price=None,
    asset_class=AssetClass.ETF,
):
    return PaperOrderIntent(
        intent_id=uuid4(),
        account_id=account_id,
        source=OrderSource.HUMAN,
        source_reference_id=uuid4(),
        symbol="SPY",
        asset_class=asset_class,
        side=side,
        quantity=quantity,
        order_type=order_type,
        limit_price=limit_price,
        time_in_force=TimeInForce.DAY,
        status=status,
        idempotency_key=f"paper-adapter-{uuid4()}",
        created_at=timestamp(),
    )


def timestamp():
    return datetime(2026, 6, 20, 14, 30)
```

- [ ] **Step 2: Run the focused adapter test and verify it fails for missing adapter**

Run on Ubuntu temporary clone:

```bash
ssh yasin-ubuntu 'cd /tmp/<slice6-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q tests/test_paper_trading_adapter.py --tb=short'
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.paper_trading.adapter'`.

## Task 2: Add Repository Helpers for Paper Simulation

**Files:**
- Modify: `backend/app/paper_trading/repository.py`
- Test: `backend/tests/test_paper_trading_adapter.py`

- [ ] **Step 1: Add account and position helper methods**

Add these methods inside `PaperTradingRepository`:

```python
    def update_account_cash(self, account_id: UUID, current_cash: float) -> PaperAccount | None:
        model = self.session.get(PaperAccountModel, account_id)
        if model is None:
            return None
        model.current_cash = current_cash
        self.session.commit()
        self.session.refresh(model)
        return to_account(model)

    def get_position_by_account_symbol_asset(
        self,
        account_id: UUID,
        symbol: str,
        asset_class: AssetClass,
    ) -> PaperPosition | None:
        model = self.session.scalar(
            select(PaperPositionModel)
            .where(PaperPositionModel.account_id == account_id)
            .where(PaperPositionModel.symbol == symbol)
            .where(PaperPositionModel.asset_class == asset_class.value)
        )
        return to_position(model) if model else None

    def list_positions_for_account(self, account_id: UUID) -> list[PaperPosition]:
        models = self.session.scalars(
            select(PaperPositionModel)
            .where(PaperPositionModel.account_id == account_id)
            .order_by(PaperPositionModel.symbol.asc(), PaperPositionModel.asset_class.asc())
        ).all()
        return [to_position(model) for model in models]
```

- [ ] **Step 2: Run the focused adapter test and verify it still fails for missing adapter**

Run:

```bash
ssh yasin-ubuntu 'cd /tmp/<slice6-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q tests/test_paper_trading_adapter.py --tb=short'
```

Expected: FAIL with missing `app.paper_trading.adapter`.

## Task 3: Add Local Paper Adapter

**Files:**
- Create: `backend/app/paper_trading/adapter.py`
- Test: `backend/tests/test_paper_trading_adapter.py`

- [ ] **Step 1: Create the adapter implementation**

Create `backend/app/paper_trading/adapter.py` with this content:

```python
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from app.paper_trading.contracts import (
    AssetClass,
    AuditOutcome,
    AuditResourceType,
    OrderIntentStatus,
    OrderSide,
    OrderType,
    PaperAccount,
    PaperAuditEvent,
    PaperFill,
    PaperOrderIntent,
    PaperPosition,
)
from app.paper_trading.repository import PaperTradingRepository


OPTION_ASSET_CLASSES = {AssetClass.INDEX_OPTION, AssetClass.EQUITY_OPTION}
CANCELLABLE_STATUSES = {
    OrderIntentStatus.DRAFT,
    OrderIntentStatus.AWAITING_REVIEW,
    OrderIntentStatus.APPROVED_FOR_PAPER,
}


class PaperExecutionError(ValueError):
    pass


@dataclass(frozen=True)
class PaperExecutionResult:
    intent: PaperOrderIntent
    account: PaperAccount
    position: PaperPosition | None
    fill: PaperFill | None


def execute_paper_intent(
    repository: PaperTradingRepository,
    intent_id: UUID,
    *,
    market_price: float,
    filled_at: datetime,
) -> PaperExecutionResult:
    intent = require_intent(repository, intent_id)
    if intent.status != OrderIntentStatus.APPROVED_FOR_PAPER:
        raise PaperExecutionError("intent_not_approved_for_paper")
    if market_price <= 0:
        raise PaperExecutionError("market_price_not_positive")

    account = require_account(repository, intent.account_id)
    fill_price = resolve_fill_price(intent, market_price)
    notional = calculate_notional(intent, fill_price)

    if intent.side == OrderSide.BUY:
        if account.current_cash < notional:
            append_event(repository, intent.intent_id, "insufficient_cash", "Paper buy rejected: insufficient cash.", filled_at)
            raise PaperExecutionError("insufficient_cash")
        account = require_account_update(repository, account.account_id, round(account.current_cash - notional, 4))
        position = upsert_buy_position(repository, intent, fill_price, filled_at)
    else:
        position = repository.get_position_by_account_symbol_asset(intent.account_id, intent.symbol, intent.asset_class)
        if position is None or position.quantity < intent.quantity:
            append_event(
                repository,
                intent.intent_id,
                "insufficient_position",
                "Paper sell rejected: insufficient position.",
                filled_at,
            )
            raise PaperExecutionError("insufficient_position")
        account = require_account_update(repository, account.account_id, round(account.current_cash + notional, 4))
        position = upsert_sell_position(repository, intent, position, filled_at)

    fill = PaperFill(
        fill_id=uuid4(),
        intent_id=intent.intent_id,
        account_id=intent.account_id,
        symbol=intent.symbol,
        asset_class=intent.asset_class,
        side=intent.side,
        quantity=intent.quantity,
        fill_price=fill_price,
        filled_at=filled_at,
    )
    repository.save_fill(fill)
    updated_intent = require_status_update(repository, intent.intent_id, OrderIntentStatus.PAPER_FILLED)
    append_event(repository, intent.intent_id, "paper_filled", "Paper intent filled by local simulation.", filled_at)
    return PaperExecutionResult(intent=updated_intent, account=account, position=position, fill=fill)


def cancel_paper_intent(
    repository: PaperTradingRepository,
    intent_id: UUID,
    *,
    message: str,
    cancelled_at: datetime | None = None,
) -> PaperExecutionResult:
    intent = require_intent(repository, intent_id)
    if intent.status not in CANCELLABLE_STATUSES:
        raise PaperExecutionError("intent_cannot_be_cancelled")
    timestamp = cancelled_at or intent.created_at
    updated_intent = require_status_update(repository, intent.intent_id, OrderIntentStatus.PAPER_CANCELLED)
    append_event(repository, intent.intent_id, "paper_cancelled", message, timestamp, outcome=AuditOutcome.DENIED)
    return PaperExecutionResult(
        intent=updated_intent,
        account=require_account(repository, intent.account_id),
        position=None,
        fill=None,
    )


def resolve_fill_price(intent: PaperOrderIntent, market_price: float) -> float:
    if intent.order_type == OrderType.LIMIT:
        return require_price(intent.limit_price)
    return require_price(market_price)


def require_price(price: float | None) -> float:
    if price is None or price <= 0:
        raise PaperExecutionError("fill_price_not_positive")
    return price


def calculate_notional(intent: PaperOrderIntent, fill_price: float) -> float:
    return round(intent.quantity * fill_price * multiplier_for(intent.asset_class), 4)


def multiplier_for(asset_class: AssetClass) -> int:
    return 100 if asset_class in OPTION_ASSET_CLASSES else 1


def upsert_buy_position(
    repository: PaperTradingRepository,
    intent: PaperOrderIntent,
    fill_price: float,
    updated_at: datetime,
) -> PaperPosition:
    existing = repository.get_position_by_account_symbol_asset(intent.account_id, intent.symbol, intent.asset_class)
    if existing is None:
        position = PaperPosition(
            position_id=uuid4(),
            account_id=intent.account_id,
            symbol=intent.symbol,
            asset_class=intent.asset_class,
            quantity=intent.quantity,
            average_price=fill_price,
            updated_at=updated_at,
        )
    else:
        total_quantity = existing.quantity + intent.quantity
        average_price = ((existing.quantity * existing.average_price) + (intent.quantity * fill_price)) / total_quantity
        position = PaperPosition(
            position_id=existing.position_id,
            account_id=existing.account_id,
            symbol=existing.symbol,
            asset_class=existing.asset_class,
            quantity=total_quantity,
            average_price=round(average_price, 4),
            updated_at=updated_at,
        )
    return repository.save_position(position)


def upsert_sell_position(
    repository: PaperTradingRepository,
    intent: PaperOrderIntent,
    existing: PaperPosition,
    updated_at: datetime,
) -> PaperPosition:
    remaining_quantity = round(existing.quantity - intent.quantity, 8)
    position = PaperPosition(
        position_id=existing.position_id,
        account_id=existing.account_id,
        symbol=existing.symbol,
        asset_class=existing.asset_class,
        quantity=remaining_quantity,
        average_price=existing.average_price if remaining_quantity > 0 else 0,
        updated_at=updated_at,
    )
    return repository.save_position(position)


def require_intent(repository: PaperTradingRepository, intent_id: UUID) -> PaperOrderIntent:
    intent = repository.get_order_intent(intent_id)
    if intent is None:
        raise PaperExecutionError("paper_intent_not_found")
    return intent


def require_account(repository: PaperTradingRepository, account_id: UUID) -> PaperAccount:
    account = repository.get_account(account_id)
    if account is None:
        raise PaperExecutionError("paper_account_not_found")
    return account


def require_account_update(repository: PaperTradingRepository, account_id: UUID, current_cash: float) -> PaperAccount:
    account = repository.update_account_cash(account_id, current_cash)
    if account is None:
        raise PaperExecutionError("paper_account_not_found")
    return account


def require_status_update(
    repository: PaperTradingRepository,
    intent_id: UUID,
    status: OrderIntentStatus,
) -> PaperOrderIntent:
    intent = repository.update_order_intent_status(intent_id, status)
    if intent is None:
        raise PaperExecutionError("paper_intent_not_found")
    return intent


def append_event(
    repository: PaperTradingRepository,
    intent_id: UUID,
    reason_code: str,
    message: str,
    created_at: datetime,
    *,
    outcome: AuditOutcome = AuditOutcome.SUCCESS,
) -> PaperAuditEvent:
    return repository.append_audit_event(
        PaperAuditEvent(
            event_id=uuid4(),
            actor_type="human",
            resource_type=AuditResourceType.ORDER_INTENT,
            resource_id=intent_id,
            action="paper_simulation",
            outcome=outcome,
            reason_code=reason_code,
            message=message,
            created_at=created_at,
        )
    )
```

- [ ] **Step 2: Run adapter tests**

Run:

```bash
ssh yasin-ubuntu 'cd /tmp/<slice6-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q tests/test_paper_trading_adapter.py --tb=short'
```

Expected: PASS.

## Task 4: Add Paper Submit and Cancel API Tests

**Files:**
- Modify: `backend/tests/test_paper_trading_api.py`

- [ ] **Step 1: Add imports for adapter API test cleanup assertions**

Keep the existing imports in `backend/tests/test_paper_trading_api.py`. No new top-level imports are required for the tests below.

- [ ] **Step 2: Add paper submit API test**

Add this test after `test_paper_intent_api_approves_and_rejects_after_review`:

```python
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
        fills = repository.list_fills_for_intent(intent_id)
        positions = repository.list_positions_for_account(account_id)
        assert account.current_cash == 99_000
        assert len(fills) == 1
        assert fills[0].fill_price == 500
        assert positions[0].quantity == 2
        assert positions[0].average_price == 500
    finally:
        session.close()
```

- [ ] **Step 3: Add paper submit gate test**

Add:

```python
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
```

- [ ] **Step 4: Add paper cancel API test**

Add:

```python
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
```

- [ ] **Step 5: Add cancel-after-fill rejection API test**

Add:

```python
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
```

- [ ] **Step 6: Run API tests and verify they fail for missing endpoints**

Run:

```bash
ssh yasin-ubuntu 'cd /tmp/<slice6-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q tests/test_paper_trading_api.py --tb=short'
```

Expected: FAIL with 404 responses for `/paper-submit` and `/cancel`.

## Task 5: Add Paper Submit and Cancel Endpoints

**Files:**
- Modify: `backend/app/paper_trading/router.py`
- Test: `backend/tests/test_paper_trading_api.py`

- [ ] **Step 1: Add adapter imports**

In `backend/app/paper_trading/router.py`, add:

```python
from app.paper_trading.adapter import PaperExecutionError, cancel_paper_intent, execute_paper_intent
```

- [ ] **Step 2: Add request schemas**

After `PaperReviewRequest`, add:

```python
class PaperSubmitRequest(BaseModel):
    market_price: float = Field(gt=0, allow_inf_nan=False)


class PaperCancelRequest(BaseModel):
    message: str = Field(min_length=1, max_length=500)
```

- [ ] **Step 3: Add paper submit endpoint**

After `review_paper_intent`, add:

```python
@router.post("/intents/{intent_id}/paper-submit", response_model=PaperIntentResponse)
def submit_paper_intent(
    intent_id: UUID,
    request: PaperSubmitRequest,
    session: Session = Depends(get_db_session),
):
    repository = PaperTradingRepository(session)
    try:
        result = execute_paper_intent(
            repository,
            intent_id,
            market_price=request.market_price,
            filled_at=utc_now(),
        )
    except PaperExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return build_response(repository, result.intent)
```

- [ ] **Step 4: Add paper cancel endpoint**

Add:

```python
@router.post("/intents/{intent_id}/cancel", response_model=PaperIntentResponse)
def cancel_paper_intent_endpoint(
    intent_id: UUID,
    request: PaperCancelRequest,
    session: Session = Depends(get_db_session),
):
    repository = PaperTradingRepository(session)
    try:
        result = cancel_paper_intent(repository, intent_id, message=request.message, cancelled_at=utc_now())
    except PaperExecutionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return build_response(repository, result.intent)
```

- [ ] **Step 5: Run API tests**

Run:

```bash
ssh yasin-ubuntu 'cd /tmp/<slice6-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q tests/test_paper_trading_api.py --tb=short'
```

Expected: PASS.

## Task 6: Run Safety Grep and Backend Regression

**Files:**
- No file changes.

- [ ] **Step 1: Confirm no broker, live execution, or network implementation was introduced**

Run:

```bash
rg -n "broker|live execution|place_order|submit_order|ibkr|alpaca|order_id|account_number|requests\\.|httpx|aiohttp|MCP|agent scope|T scope" backend/app/paper_trading backend/tests/test_paper_trading_adapter.py backend/tests/test_paper_trading_api.py backend/app/main.py
```

Expected: no output except negative test assertions. If implementation code contains broker routes, broker SDK names, live order ids, account numbers, network libraries, MCP trading tools, or agent trading scope, stop and remove them.

- [ ] **Step 2: Run focused paper tests on Ubuntu**

```bash
ssh yasin-ubuntu 'cd /tmp/<slice6-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q tests/test_paper_trading_contracts.py tests/test_paper_trading_risk_guard.py tests/test_paper_trading_repository.py tests/test_paper_trading_api.py tests/test_paper_trading_adapter.py --tb=short'
```

Expected: PASS.

- [ ] **Step 3: Run full backend regression on Ubuntu**

```bash
ssh yasin-ubuntu 'cd /tmp/<slice6-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q --tb=short'
```

Expected: PASS.

## Task 7: Update Documentation After Verification

**Files:**
- Modify: `docs/roadmap/phase-5-roadmap.md`
- Modify: `PROJECT.md`

- [ ] **Step 1: Update Slice 6 roadmap status**

Replace the Slice 6 section in `docs/roadmap/phase-5-roadmap.md` with:

```markdown
### Slice 6: Paper Adapter and Position Simulation

Status: implemented and validated on 2026-06-20.

Implemented:

- Local deterministic paper adapter for approved paper intents.
- Simulated paper fills with caller-supplied deterministic market prices.
- Cash and position updates for buy and sell flows.
- Rejection paths for insufficient cash, insufficient position, and non-approved intents.
- Cancel flow for unfilled intents.
- Human-facing paper submit and cancel API endpoints.
- Broker integration, live execution, network calls, broker credentials, agent trading scope, and MCP trading tools remain out of scope.

Implementation plan:

- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-5-slice-6-paper-adapter-simulation.md`

Verification:

- Record the exact Ubuntu isolated adapter test output line from Task 6.
- Record the exact Ubuntu isolated API test output line from Task 6.
- Record the exact Ubuntu isolated Slice 2+3+4+5+6 focused test output line from Task 6.
- Record the exact Ubuntu isolated backend regression output line from Task 6.
- Safety grep only matched planned negative broker/live/order_id test assertions and found no broker SDK, broker credentials, live order methods, network libraries, MCP trading tools, or agent trading scope implementation.
```

- [ ] **Step 2: Update project status snapshot**

Update the current Phase 5 bullet in `PROJECT.md` to:

```markdown
- Current Phase 5 state: Phase 5 is in paper-only backend implementation. Phase 4 completed the approved research-only Strategy Lab experiment workbench scope. Phase 5 now has paper-only architecture documentation, backend domain contracts, pure RiskGuard evaluator, SQLAlchemy persistence models, SQL schema, repository methods, append-only audit event persistence, human-facing paper intent API endpoints, and a local deterministic paper adapter for approved paper intents with simulated fills, cash updates, position updates, and unfilled-intent cancellation. UI promotion flows, live broker execution, broker credentials, broker account mutation, AI-directed live trading, trading-scope MCP tools, network execution, and automatic paper-to-live promotion remain out of scope.
```

## Task 8: Final Verification, Commit, and Push

**Files:**
- Stage all files touched in this implementation.

- [ ] **Step 1: Run whitespace check**

```bash
git diff --check
```

Expected: no output.

- [ ] **Step 2: Run final safety grep**

```bash
rg -n "broker|live execution|place_order|submit_order|ibkr|alpaca|order_id|account_number|requests\\.|httpx|aiohttp|MCP|agent scope|T scope" backend/app/paper_trading backend/tests/test_paper_trading_adapter.py backend/tests/test_paper_trading_api.py backend/app/main.py
```

Expected: no output except negative test assertions.

- [ ] **Step 3: Run final focused paper tests on Ubuntu**

```bash
ssh yasin-ubuntu 'cd /tmp/<slice6-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q tests/test_paper_trading_contracts.py tests/test_paper_trading_risk_guard.py tests/test_paper_trading_repository.py tests/test_paper_trading_api.py tests/test_paper_trading_adapter.py --tb=short'
```

Expected: PASS.

- [ ] **Step 4: Run final full backend regression on Ubuntu**

```bash
ssh yasin-ubuntu 'cd /tmp/<slice6-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q --tb=short'
```

Expected: PASS.

- [ ] **Step 5: Stage implementation files**

```bash
git add backend/app/paper_trading/adapter.py backend/app/paper_trading/repository.py backend/app/paper_trading/router.py backend/tests/test_paper_trading_adapter.py backend/tests/test_paper_trading_api.py docs/roadmap/phase-5-roadmap.md PROJECT.md
```

- [ ] **Step 6: Commit**

```bash
git commit -m "feat: add paper trading simulation adapter"
```

- [ ] **Step 7: Push**

```bash
git push origin aquantlens-us
```

## Self-Review Checklist

- Spec coverage: Slice 6 implements local deterministic paper simulation, cash/position updates, and cancellation only.
- Completeness scan: this plan defines concrete tests, repository helpers, adapter behavior, API endpoints, verification commands, and documentation update wording.
- Type consistency: route names, status values, repository helper names, adapter function names, and reason codes are consistent across tasks.
- Safety boundary: implementation must not add broker credentials, live order ids, broker routes, broker SDK calls, network calls, MCP trading tools, agent trading scope, frontend UI, or paper-to-live promotion.
