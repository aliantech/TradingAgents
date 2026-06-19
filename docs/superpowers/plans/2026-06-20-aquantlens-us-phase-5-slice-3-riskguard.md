# AQuantLens US Phase 5 Slice 3 RiskGuard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a pure paper-only RiskGuard service and tests that decide whether a `PaperOrderIntent` can proceed to paper review without adding persistence, API routes, frontend UI, broker adapters, or live execution behavior.

**Architecture:** Keep RiskGuard inside the existing `app.paper_trading` package as a pure Python service over the Slice 2 contracts. The service receives an intent, paper account, allowlists, paper limits, and optional option metadata, then returns a `RiskDecision` with deterministic reason codes. It must not mutate intents, create fills, update positions, call brokers, read credentials, or depend on database sessions.

**Tech Stack:** Python 3.12, Pydantic v2 contract models, pytest, FastAPI backend package layout.

---

## Scope

This plan implements Phase 5 Slice 3 only.

Included:

- `RiskGuardInput`
- `RiskGuardLimits`
- `OptionIntentMetadata`
- `evaluate_order_intent`
- deterministic pass/reject reason codes
- focused unit tests
- safety grep checks
- roadmap and project status updates

Excluded:

- database persistence
- SQL migrations
- API endpoints
- frontend UI
- paper execution adapter
- cash or position mutation
- audit persistence
- broker integration
- live execution
- MCP trading tools

## File Structure

- Modify `backend/app/paper_trading/contracts.py`
  - Add `RiskGuardLimits`, `OptionIntentMetadata`, and `RiskGuardInput`.
- Modify `backend/app/paper_trading/__init__.py`
  - Export the new RiskGuard input contracts and evaluator.
- Create `backend/app/paper_trading/risk_guard.py`
  - Implement pure RiskGuard decision logic.
- Create `backend/tests/test_paper_trading_risk_guard.py`
  - Cover pass path and each deterministic rejection reason.
- Modify `docs/roadmap/phase-5-roadmap.md`
  - Mark Slice 3 as implemented after verification.
- Modify `PROJECT.md`
  - Update current Phase 5 state after Slice 3 is verified.

## Reason Codes

Use these exact reason codes:

- `paper_account_inactive`
- `symbol_not_allowlisted`
- `asset_class_not_allowed`
- `quantity_not_positive`
- `limit_price_not_positive`
- `estimated_notional_exceeds_intent_limit`
- `estimated_daily_notional_exceeds_limit`
- `option_metadata_required`
- `candidate_source_required`
- `risk_checks_passed`

## Task 1: Add Failing RiskGuard Tests

**Files:**
- Create: `backend/tests/test_paper_trading_risk_guard.py`

- [ ] **Step 1: Write the failing test file**

Create `backend/tests/test_paper_trading_risk_guard.py` with this content:

```python
from datetime import UTC, date, datetime
from uuid import uuid4

from app.paper_trading.contracts import (
    AssetClass,
    OrderIntentStatus,
    OrderSide,
    OrderSource,
    OrderType,
    PaperAccount,
    PaperAccountStatus,
    PaperOrderIntent,
    RiskDecisionResult,
    RiskGuardInput,
    RiskGuardLimits,
    TimeInForce,
)
from app.paper_trading.risk_guard import evaluate_order_intent


def test_risk_guard_passes_valid_equity_intent():
    decision = evaluate_order_intent(
        RiskGuardInput(
            account=active_account(),
            intent=equity_intent(),
            allowed_symbols={"SPY"},
            allowed_asset_classes={AssetClass.ETF},
            limits=RiskGuardLimits(
                max_notional_per_intent=2_000,
                max_daily_notional=5_000,
                current_daily_notional=1_000,
            ),
            candidate_experiment_ids={SOURCE_REFERENCE_ID},
        )
    )

    assert decision.result == RiskDecisionResult.PASS
    assert decision.reason_codes == ["risk_checks_passed"]
    assert decision.estimated_notional == 1_000


def test_risk_guard_rejects_inactive_account():
    decision = evaluate_order_intent(
        base_input(account=active_account(status=PaperAccountStatus.PAUSED))
    )

    assert decision.result == RiskDecisionResult.REJECT
    assert decision.reason_codes == ["paper_account_inactive"]


def test_risk_guard_rejects_symbol_outside_allowlist():
    decision = evaluate_order_intent(base_input(allowed_symbols={"QQQ"}))

    assert decision.result == RiskDecisionResult.REJECT
    assert decision.reason_codes == ["symbol_not_allowlisted"]


def test_risk_guard_rejects_asset_class_outside_scope():
    decision = evaluate_order_intent(base_input(allowed_asset_classes={AssetClass.EQUITY}))

    assert decision.result == RiskDecisionResult.REJECT
    assert decision.reason_codes == ["asset_class_not_allowed"]


def test_risk_guard_rejects_non_positive_quantity_even_if_contract_was_bypassed():
    intent = equity_intent()
    object.__setattr__(intent, "quantity", 0)

    decision = evaluate_order_intent(base_input(intent=intent))

    assert decision.result == RiskDecisionResult.REJECT
    assert decision.reason_codes == ["quantity_not_positive"]
    assert decision.estimated_notional == 0


def test_risk_guard_rejects_non_positive_limit_price_even_if_contract_was_bypassed():
    intent = equity_intent(order_type=OrderType.LIMIT, limit_price=500)
    object.__setattr__(intent, "limit_price", 0)

    decision = evaluate_order_intent(base_input(intent=intent))

    assert decision.result == RiskDecisionResult.REJECT
    assert decision.reason_codes == ["limit_price_not_positive"]


def test_risk_guard_rejects_intent_notional_above_limit():
    decision = evaluate_order_intent(
        base_input(
            limits=RiskGuardLimits(
                max_notional_per_intent=999,
                max_daily_notional=5_000,
                current_daily_notional=0,
            )
        )
    )

    assert decision.result == RiskDecisionResult.REJECT
    assert decision.reason_codes == ["estimated_notional_exceeds_intent_limit"]
    assert decision.estimated_notional == 1_000


def test_risk_guard_rejects_daily_notional_above_limit():
    decision = evaluate_order_intent(
        base_input(
            limits=RiskGuardLimits(
                max_notional_per_intent=2_000,
                max_daily_notional=1_500,
                current_daily_notional=750,
            )
        )
    )

    assert decision.result == RiskDecisionResult.REJECT
    assert decision.reason_codes == ["estimated_daily_notional_exceeds_limit"]
    assert decision.estimated_notional == 1_000


def test_risk_guard_requires_option_metadata_for_option_intents():
    option_intent = equity_intent(
        symbol="SPY260620C00500000",
        asset_class=AssetClass.EQUITY_OPTION,
        order_type=OrderType.LIMIT,
        limit_price=5,
    )

    decision = evaluate_order_intent(
        base_input(
            intent=option_intent,
            allowed_symbols={"SPY260620C00500000"},
            allowed_asset_classes={AssetClass.EQUITY_OPTION},
            option_metadata=None,
        )
    )

    assert decision.result == RiskDecisionResult.REJECT
    assert decision.reason_codes == ["option_metadata_required"]


def test_risk_guard_passes_option_intent_with_metadata():
    option_intent = equity_intent(
        symbol="SPY260620C00500000",
        asset_class=AssetClass.EQUITY_OPTION,
        order_type=OrderType.LIMIT,
        limit_price=5,
    )

    decision = evaluate_order_intent(
        base_input(
            intent=option_intent,
            allowed_symbols={"SPY260620C00500000"},
            allowed_asset_classes={AssetClass.EQUITY_OPTION},
            option_metadata={
                "underlying_symbol": "SPY",
                "expiry": date(2026, 6, 20),
                "strike": 500,
                "option_type": "call",
            },
        )
    )

    assert decision.result == RiskDecisionResult.PASS
    assert decision.reason_codes == ["risk_checks_passed"]
    assert decision.estimated_notional == 500


def test_risk_guard_requires_candidate_source_reference():
    decision = evaluate_order_intent(base_input(candidate_experiment_ids=set()))

    assert decision.result == RiskDecisionResult.REJECT
    assert decision.reason_codes == ["candidate_source_required"]


def test_risk_guard_returns_first_deterministic_rejection():
    decision = evaluate_order_intent(
        base_input(
            account=active_account(status=PaperAccountStatus.PAUSED),
            allowed_symbols={"QQQ"},
        )
    )

    assert decision.result == RiskDecisionResult.REJECT
    assert decision.reason_codes == ["paper_account_inactive"]


SOURCE_REFERENCE_ID = uuid4()


def base_input(
    *,
    account=None,
    intent=None,
    allowed_symbols=None,
    allowed_asset_classes=None,
    limits=None,
    option_metadata=None,
    candidate_experiment_ids=None,
):
    return RiskGuardInput(
        account=account or active_account(),
        intent=intent or equity_intent(),
        allowed_symbols=allowed_symbols or {"SPY"},
        allowed_asset_classes=allowed_asset_classes or {AssetClass.ETF},
        limits=limits
        or RiskGuardLimits(
            max_notional_per_intent=2_000,
            max_daily_notional=5_000,
            current_daily_notional=1_000,
        ),
        option_metadata=option_metadata,
        candidate_experiment_ids=(
            {SOURCE_REFERENCE_ID}
            if candidate_experiment_ids is None
            else candidate_experiment_ids
        ),
    )


def active_account(status=PaperAccountStatus.ACTIVE):
    return PaperAccount(
        account_id=uuid4(),
        name="Default paper account",
        base_currency="USD",
        starting_cash=100_000,
        current_cash=100_000,
        status=status,
        created_at=timestamp(),
    )


def equity_intent(
    *,
    symbol="SPY",
    asset_class=AssetClass.ETF,
    order_type=OrderType.MARKET,
    limit_price=None,
):
    return PaperOrderIntent(
        intent_id=uuid4(),
        account_id=uuid4(),
        source=OrderSource.HUMAN,
        source_reference_id=SOURCE_REFERENCE_ID,
        symbol=symbol,
        asset_class=asset_class,
        side=OrderSide.BUY,
        quantity=2,
        order_type=order_type,
        limit_price=limit_price,
        time_in_force=TimeInForce.DAY,
        status=OrderIntentStatus.DRAFT,
        idempotency_key=f"riskguard-{symbol}-{uuid4()}",
        created_at=timestamp(),
    )


def timestamp():
    return datetime(2026, 6, 20, 13, 30, tzinfo=UTC)
```

- [ ] **Step 2: Run the focused test and verify it fails for missing RiskGuard**

Run on Ubuntu:

```bash
ssh yasin-ubuntu 'cd /home/yasin/workspace/TradingAgents/backend && PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_paper_trading_risk_guard.py --tb=short'
```

Expected: FAIL with `ImportError` or `ModuleNotFoundError` because `RiskGuardInput`, `RiskGuardLimits`, or `app.paper_trading.risk_guard` does not exist.

## Task 2: Add RiskGuard Input Contracts

**Files:**
- Modify: `backend/app/paper_trading/contracts.py`
- Modify: `backend/app/paper_trading/__init__.py`
- Test: `backend/tests/test_paper_trading_risk_guard.py`

- [ ] **Step 1: Add the input contract classes**

Append this code to `backend/app/paper_trading/contracts.py` after `PaperAuditEvent`:

```python
class RiskGuardLimits(StrictContract):
    max_notional_per_intent: float = Field(gt=0, allow_inf_nan=False)
    max_daily_notional: float = Field(gt=0, allow_inf_nan=False)
    current_daily_notional: float = Field(ge=0, allow_inf_nan=False)


class OptionIntentMetadata(StrictContract):
    underlying_symbol: str = Field(min_length=1, max_length=64)
    expiry: datetime | date
    strike: float = Field(gt=0, allow_inf_nan=False)
    option_type: str = Field(pattern="^(call|put)$")


class RiskGuardInput(StrictContract):
    account: PaperAccount
    intent: PaperOrderIntent
    allowed_symbols: set[str] = Field(min_length=1)
    allowed_asset_classes: set[AssetClass] = Field(min_length=1)
    limits: RiskGuardLimits
    option_metadata: OptionIntentMetadata | None = None
    candidate_experiment_ids: set[UUID] = Field(default_factory=set)
```

Also add `date` to the datetime import:

```python
from datetime import date, datetime
```

- [ ] **Step 2: Export the new contracts**

In `backend/app/paper_trading/__init__.py`, add `OptionIntentMetadata`, `RiskGuardInput`, and `RiskGuardLimits` to the import list and `__all__`.

- [ ] **Step 3: Run the focused test and verify the failure moves to missing evaluator**

Run on Ubuntu:

```bash
ssh yasin-ubuntu 'cd /home/yasin/workspace/TradingAgents/backend && PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_paper_trading_risk_guard.py --tb=short'
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.paper_trading.risk_guard'`.

## Task 3: Implement Pure RiskGuard Evaluator

**Files:**
- Create: `backend/app/paper_trading/risk_guard.py`
- Modify: `backend/app/paper_trading/__init__.py`
- Test: `backend/tests/test_paper_trading_risk_guard.py`

- [ ] **Step 1: Create the RiskGuard service**

Create `backend/app/paper_trading/risk_guard.py` with this content:

```python
from uuid import uuid4

from app.paper_trading.contracts import (
    AssetClass,
    OrderType,
    PaperAccountStatus,
    RiskDecision,
    RiskDecisionResult,
    RiskGuardInput,
)


OPTION_ASSET_CLASSES = {AssetClass.INDEX_OPTION, AssetClass.EQUITY_OPTION}


def evaluate_order_intent(risk_input: RiskGuardInput) -> RiskDecision:
    intent = risk_input.intent
    estimated_notional = estimate_notional(risk_input)

    if risk_input.account.status != PaperAccountStatus.ACTIVE:
        return reject(intent.intent_id, "paper_account_inactive", estimated_notional)
    if intent.symbol not in risk_input.allowed_symbols:
        return reject(intent.intent_id, "symbol_not_allowlisted", estimated_notional)
    if intent.asset_class not in risk_input.allowed_asset_classes:
        return reject(intent.intent_id, "asset_class_not_allowed", estimated_notional)
    if intent.quantity <= 0:
        return reject(intent.intent_id, "quantity_not_positive", estimated_notional)
    if intent.order_type == OrderType.LIMIT and (intent.limit_price is None or intent.limit_price <= 0):
        return reject(intent.intent_id, "limit_price_not_positive", estimated_notional)
    if estimated_notional > risk_input.limits.max_notional_per_intent:
        return reject(intent.intent_id, "estimated_notional_exceeds_intent_limit", estimated_notional)
    if (
        risk_input.limits.current_daily_notional + estimated_notional
        > risk_input.limits.max_daily_notional
    ):
        return reject(intent.intent_id, "estimated_daily_notional_exceeds_limit", estimated_notional)
    if intent.asset_class in OPTION_ASSET_CLASSES and risk_input.option_metadata is None:
        return reject(intent.intent_id, "option_metadata_required", estimated_notional)
    if intent.source_reference_id not in risk_input.candidate_experiment_ids:
        return reject(intent.intent_id, "candidate_source_required", estimated_notional)

    return RiskDecision(
        decision_id=uuid4(),
        intent_id=intent.intent_id,
        result=RiskDecisionResult.PASS,
        reason_codes=["risk_checks_passed"],
        explanation="RiskGuard checks passed for paper simulation.",
        estimated_notional=estimated_notional,
        created_at=intent.created_at,
    )


def estimate_notional(risk_input: RiskGuardInput) -> float:
    intent = risk_input.intent
    if intent.order_type == OrderType.LIMIT and intent.limit_price is not None:
        return round(intent.quantity * intent.limit_price, 4)
    return round(intent.quantity * 500, 4)


def reject(intent_id, reason_code: str, estimated_notional: float) -> RiskDecision:
    return RiskDecision(
        decision_id=uuid4(),
        intent_id=intent_id,
        result=RiskDecisionResult.REJECT,
        reason_codes=[reason_code],
        explanation=f"RiskGuard rejected paper intent: {reason_code}.",
        estimated_notional=estimated_notional,
        created_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
    )
```

- [ ] **Step 2: Export the evaluator**

In `backend/app/paper_trading/__init__.py`, add:

```python
from app.paper_trading.risk_guard import evaluate_order_intent
```

and add `"evaluate_order_intent"` to `__all__`.

- [ ] **Step 3: Run focused RiskGuard tests**

Run on Ubuntu:

```bash
ssh yasin-ubuntu 'cd /home/yasin/workspace/TradingAgents/backend && PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_paper_trading_risk_guard.py --tb=short'
```

Expected: PASS with all RiskGuard tests passing.

## Task 4: Tighten Time and Notional Behavior

**Files:**
- Modify: `backend/app/paper_trading/risk_guard.py`
- Modify: `backend/tests/test_paper_trading_risk_guard.py`

- [ ] **Step 1: Add a test that rejection decisions preserve intent time**

Append this test to `backend/tests/test_paper_trading_risk_guard.py`:

```python
def test_risk_guard_rejection_uses_intent_created_time():
    intent = equity_intent()

    decision = evaluate_order_intent(
        base_input(
            intent=intent,
            allowed_symbols={"QQQ"},
        )
    )

    assert decision.created_at == intent.created_at
```

- [ ] **Step 2: Run the new test and verify it fails**

Run on Ubuntu:

```bash
ssh yasin-ubuntu 'cd /home/yasin/workspace/TradingAgents/backend && PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_paper_trading_risk_guard.py::test_risk_guard_rejection_uses_intent_created_time --tb=short'
```

Expected: FAIL because `reject()` currently uses current time.

- [ ] **Step 3: Make rejection decisions deterministic**

Replace the `reject` helper and call sites in `backend/app/paper_trading/risk_guard.py` so `reject()` accepts the full intent:

```python
def reject(intent, reason_code: str, estimated_notional: float) -> RiskDecision:
    return RiskDecision(
        decision_id=uuid4(),
        intent_id=intent.intent_id,
        result=RiskDecisionResult.REJECT,
        reason_codes=[reason_code],
        explanation=f"RiskGuard rejected paper intent: {reason_code}.",
        estimated_notional=estimated_notional,
        created_at=intent.created_at,
    )
```

Update each call from:

```python
return reject(intent.intent_id, "reason_code", estimated_notional)
```

to:

```python
return reject(intent, "reason_code", estimated_notional)
```

Remove the dynamic datetime import from `reject()`.

- [ ] **Step 4: Run focused RiskGuard tests**

Run on Ubuntu:

```bash
ssh yasin-ubuntu 'cd /home/yasin/workspace/TradingAgents/backend && PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_paper_trading_risk_guard.py --tb=short'
```

Expected: PASS with all RiskGuard tests passing.

## Task 5: Run Safety Grep and Backend Regression

**Files:**
- No file changes.

- [ ] **Step 1: Confirm no broker or live execution implementation was introduced**

Run:

```bash
rg -n "broker|live execution|place_order|submit_order|ibkr|alpaca|order_id|account_number|requests\\.|httpx|aiohttp" backend/app/paper_trading backend/tests/test_paper_trading_risk_guard.py
```

Expected: no output. If implementation code contains broker routes, broker SDK names, live order ids, account numbers, or network libraries, stop and remove them.

- [ ] **Step 2: Run Slice 2 and Slice 3 focused tests on Ubuntu**

```bash
ssh yasin-ubuntu 'cd /home/yasin/workspace/TradingAgents/backend && PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_paper_trading_contracts.py tests/test_paper_trading_risk_guard.py --tb=short'
```

Expected: PASS.

- [ ] **Step 3: Run full backend regression on Ubuntu**

```bash
ssh yasin-ubuntu 'cd /home/yasin/workspace/TradingAgents/backend && PYTHONPATH=. .venv/bin/python -m pytest -q --tb=short'
```

Expected: PASS.

## Task 6: Update Documentation After Verification

**Files:**
- Modify: `docs/roadmap/phase-5-roadmap.md`
- Modify: `PROJECT.md`

- [ ] **Step 1: Update Slice 3 status in the roadmap**

In `docs/roadmap/phase-5-roadmap.md`, replace:

```markdown
### Slice 3: RiskGuard Contract and Tests

Status: pending Slice 2.
```

with:

```markdown
### Slice 3: RiskGuard Contract and Tests

Status: implemented and validated on 2026-06-20.
```

Then add this under the Slice 3 heading:

```markdown
Implemented:

- Added pure `backend/app/paper_trading/risk_guard.py` evaluator.
- Added RiskGuard input contracts for limits, option metadata, and evaluation input.
- Added deterministic reason codes for account, symbol, asset class, quantity, limit price, notional, option metadata, and candidate source reference denials.
- Added focused tests for pass and rejection paths.
- Kept RiskGuard free of database, API, frontend, broker, network, credential, and execution-adapter dependencies.
```

- [ ] **Step 2: Update project status snapshot**

In `PROJECT.md`, update the current Phase 5 state paragraph so it says Slice 3 RiskGuard is implemented and validated, while persistence, APIs, adapter, UI, and broker execution remain out of scope.

Use this wording:

```markdown
- Current Phase 5 state: Phase 5 is in paper-only planning and early contract implementation. Phase 4 completed the approved research-only Strategy Lab experiment workbench scope. Phase 5 now has paper-only architecture documentation, backend domain contracts for paper accounts/order intents/risk decisions/fills/positions/audit events, and a pure RiskGuard evaluator with deterministic pass/reject reason codes. Persistence, APIs, paper adapter execution, UI promotion flows, live broker execution, broker credentials, broker account mutation, AI-directed live trading, trading-scope MCP tools, and automatic paper-to-live promotion remain out of scope.
```

- [ ] **Step 3: Run docs diff check**

```bash
git diff -- docs/roadmap/phase-5-roadmap.md PROJECT.md
```

Expected: only Slice 3 status/evidence and project snapshot changes.

## Task 7: Final Verification, Commit, and Push

**Files:**
- Stage all files touched in this implementation.

- [ ] **Step 1: Run whitespace check**

```bash
git diff --check
```

Expected: no output.

- [ ] **Step 2: Run final focused tests on Ubuntu**

```bash
ssh yasin-ubuntu 'cd /home/yasin/workspace/TradingAgents/backend && PYTHONPATH=. .venv/bin/python -m pytest -q tests/test_paper_trading_contracts.py tests/test_paper_trading_risk_guard.py --tb=short'
```

Expected: PASS.

- [ ] **Step 3: Run final full backend regression on Ubuntu**

```bash
ssh yasin-ubuntu 'cd /home/yasin/workspace/TradingAgents/backend && PYTHONPATH=. .venv/bin/python -m pytest -q --tb=short'
```

Expected: PASS.

- [ ] **Step 4: Stage implementation files**

```bash
git add backend/app/paper_trading/__init__.py backend/app/paper_trading/contracts.py backend/app/paper_trading/risk_guard.py backend/tests/test_paper_trading_risk_guard.py docs/roadmap/phase-5-roadmap.md PROJECT.md
```

- [ ] **Step 5: Commit**

```bash
git commit -m "feat: add paper trading risk guard"
```

- [ ] **Step 6: Push**

```bash
git push origin aquantlens-us
```

## Self-Review Checklist

- Spec coverage: Slice 3 implements pure RiskGuard and tests only; persistence, API, adapter, and UI are deferred.
- Placeholder scan: this plan contains no placeholders for implementation behavior.
- Type consistency: model, function, enum, and reason-code names are consistent across tests and implementation.
- Safety boundary: implementation must not add broker credentials, live order ids, broker routes, broker SDK calls, network calls, database writes, API routes, or execution adapters.
