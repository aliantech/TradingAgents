# AQuantLens US Phase 5 Slice 7 Candidate-to-Paper UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a paper-only Candidate-to-Paper UI flow in Strategy Lab so a human can create a paper intent draft from a candidate experiment, run RiskGuard, review approve/reject, and optionally submit/cancel paper simulation without adding broker, live trading, or agent trading scope.

**Architecture:** Extend the existing paper trading API with minimal paper account list/create endpoints needed by the UI, then add typed frontend API client methods and integrate them into `StrategyLabPanel`. Keep the UI inside the existing Strategy Lab surface: Candidate Review Board creates a paper draft, and a compact Paper Review panel shows intent status, RiskGuard/audit timeline, and explicit paper-only actions. No new app route, no live execution controls, no broker fields, and no automatic paper-to-live promotion.

**Tech Stack:** FastAPI, Pydantic v2, SQLAlchemy ORM, pytest, React, TypeScript, Vite, existing shadcn-style UI components, lucide-react icons.

---

## Scope

This plan implements Phase 5 Slice 7 only.

Included:

- Backend paper account list/create endpoints for UI bootstrap.
- Frontend typed API methods for paper accounts and paper intents.
- Candidate Review Board action to create a paper intent draft.
- Paper Review panel inside Strategy Lab.
- RiskGuard button with conservative defaults for paper review.
- Human approve/reject buttons.
- Paper submit/cancel buttons using existing Slice 6 endpoints.
- Loading, error, and selected-intent states.
- Frontend build verification and focused backend tests.
- Safety grep checks.
- Roadmap and project status updates.

Excluded:

- Broker integration.
- Live execution.
- Broker credentials or broker account identifiers.
- Network calls other than same-origin app API calls.
- Agent Gateway write scope.
- MCP trading tools.
- Automatic paper submit after candidate creation.
- Automatic paper-to-live promotion.
- Multi-account production account management UI.
- New top-level app navigation route.

## UX Rules

- Candidate Review Board action text must use paper terminology, such as `Paper Draft`.
- The Paper Review panel must show `paper_only`.
- Submit action text must use `Paper Submit`, not `Buy`, `Sell`, `Trade`, or `Live`.
- UI must not show broker, account number, live order id, or external order id.
- Candidate creation defaults:
  - symbol: candidate symbol
  - source_reference_id: candidate experiment id
  - asset_class: `etf` when symbol is `SPY` or `QQQ`, else `equity`
  - side: `buy`
  - quantity: `1`
  - order_type: `market`
  - time_in_force: `day`
- RiskGuard defaults:
  - allowed_symbols: selected intent symbol
  - allowed_asset_classes: selected intent asset class
  - max_notional_per_intent: `2000`
  - max_daily_notional: `5000`
  - current_daily_notional: `0`
- Paper submit defaults:
  - market_price: `500`
  - This is deterministic placeholder input for local simulation only. It is not market data fetching.

## File Structure

- Modify `backend/app/paper_trading/repository.py`
  - Add `list_accounts`.
- Modify `backend/app/paper_trading/router.py`
  - Add paper account schemas and `GET/POST /api/paper-trading/accounts`.
- Modify `backend/tests/test_paper_trading_api.py`
  - Add account list/create tests.
- Modify `frontend/src/lib/api.ts`
  - Add paper trading types and API methods.
- Modify `frontend/src/features/strategy-lab/StrategyLabPanel.tsx`
  - Add candidate-to-paper actions and paper review panel.
- Modify `docs/roadmap/phase-5-roadmap.md`
  - Mark Slice 7 implemented after verification.
- Modify `PROJECT.md`
  - Update current Phase 5 state after verification.

## Task 1: Add Backend Account API Tests

**Files:**
- Modify: `backend/tests/test_paper_trading_api.py`

- [ ] **Step 1: Add account list/create tests**

Add these tests after `test_paper_intent_create_replays_idempotency_key`:

```python
def test_paper_account_api_creates_and_lists_accounts():
    client = TestClient(app)

    create_response = client.post(
        "/api/paper-trading/accounts",
        json={
            "name": "UI paper account",
            "base_currency": "USD",
            "starting_cash": 100_000,
        },
    )

    assert create_response.status_code == 201
    account = create_response.json()["account"]
    assert account["name"] == "UI paper account"
    assert account["base_currency"] == "USD"
    assert account["starting_cash"] == 100_000
    assert account["current_cash"] == 100_000
    assert account["status"] == "active"

    list_response = client.get("/api/paper-trading/accounts")
    assert list_response.status_code == 200
    assert [row["account_id"] for row in list_response.json()["accounts"]] == [account["account_id"]]
```

Add:

```python
def test_paper_account_api_does_not_expose_broker_or_live_fields():
    client = TestClient(app)
    response = client.post(
        "/api/paper-trading/accounts",
        json={
            "name": "Safety paper account",
            "base_currency": "USD",
            "starting_cash": 100_000,
        },
    )

    text = response.text.lower()
    assert "broker" not in text
    assert "live" not in text
    assert "account_number" not in text
```

- [ ] **Step 2: Run backend API test and verify it fails for missing account endpoints**

Run on Ubuntu temporary clone:

```bash
ssh yasin-ubuntu 'cd /tmp/<slice7-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q tests/test_paper_trading_api.py --tb=short'
```

Expected: FAIL with 404 responses for `/api/paper-trading/accounts`.

## Task 2: Add Backend Account Endpoints

**Files:**
- Modify: `backend/app/paper_trading/repository.py`
- Modify: `backend/app/paper_trading/router.py`
- Test: `backend/tests/test_paper_trading_api.py`

- [ ] **Step 1: Add `list_accounts` repository helper**

In `PaperTradingRepository`, after `get_account`, add:

```python
    def list_accounts(self) -> list[PaperAccount]:
        models = self.session.scalars(select(PaperAccountModel).order_by(PaperAccountModel.created_at.asc())).all()
        return [to_account(model) for model in models]
```

- [ ] **Step 2: Add account schemas and endpoints**

In `backend/app/paper_trading/router.py`, import `PaperAccount` and `PaperAccountStatus` from contracts if not already imported.

Add these schemas after `PaperCancelRequest`:

```python
class PaperAccountCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    base_currency: str = Field(default="USD", min_length=3, max_length=3)
    starting_cash: float = Field(gt=0, allow_inf_nan=False)


class PaperAccountItem(BaseModel):
    account_id: UUID
    name: str
    base_currency: str
    starting_cash: float
    current_cash: float
    status: str
    created_at: str


class PaperAccountResponse(BaseModel):
    scope: str = "paper_only"
    account: PaperAccountItem


class PaperAccountListResponse(BaseModel):
    scope: str = "paper_only"
    accounts: list[PaperAccountItem]
```

Add these endpoints before `/intents` endpoints:

```python
@router.get("/accounts", response_model=PaperAccountListResponse)
def list_paper_accounts(session: Session = Depends(get_db_session)):
    repository = PaperTradingRepository(session)
    return PaperAccountListResponse(accounts=[to_account_item(account) for account in repository.list_accounts()])


@router.post("/accounts", response_model=PaperAccountResponse, status_code=status.HTTP_201_CREATED)
def create_paper_account(
    request: PaperAccountCreateRequest,
    session: Session = Depends(get_db_session),
):
    account = PaperAccount(
        account_id=uuid4(),
        name=request.name,
        base_currency=request.base_currency.upper(),
        starting_cash=request.starting_cash,
        current_cash=request.starting_cash,
        status=PaperAccountStatus.ACTIVE,
        created_at=utc_now(),
    )
    repository = PaperTradingRepository(session)
    repository.save_account(account)
    return PaperAccountResponse(account=to_account_item(account))
```

Add helper near `to_intent_item`:

```python
def to_account_item(account: PaperAccount) -> PaperAccountItem:
    return PaperAccountItem(
        account_id=account.account_id,
        name=account.name,
        base_currency=account.base_currency,
        starting_cash=account.starting_cash,
        current_cash=account.current_cash,
        status=account.status.value,
        created_at=account.created_at.isoformat(),
    )
```

- [ ] **Step 3: Run backend API tests**

Run:

```bash
ssh yasin-ubuntu 'cd /tmp/<slice7-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q tests/test_paper_trading_api.py --tb=short'
```

Expected: PASS.

## Task 3: Add Frontend Paper API Client Types and Methods

**Files:**
- Modify: `frontend/src/lib/api.ts`

- [ ] **Step 1: Add paper trading types**

After `StrategyExperimentCandidateBoardResponse`, add:

```ts
export type PaperAccount = {
  account_id: string;
  name: string;
  base_currency: string;
  starting_cash: number;
  current_cash: number;
  status: "active" | "paused" | "archived";
  created_at: string;
};

export type PaperAccountListResponse = {
  scope: "paper_only";
  accounts: PaperAccount[];
};

export type PaperAccountResponse = {
  scope: "paper_only";
  account: PaperAccount;
};

export type PaperIntentStatus =
  | "draft"
  | "risk_rejected"
  | "awaiting_review"
  | "approved_for_paper"
  | "paper_submitted"
  | "paper_filled"
  | "paper_cancelled";

export type PaperIntent = {
  intent_id: string;
  account_id: string;
  source: string;
  source_reference_id: string;
  symbol: string;
  asset_class: "equity" | "etf" | "index-option" | "equity-option";
  side: "buy" | "sell";
  quantity: number;
  order_type: "market" | "limit";
  limit_price: number | null;
  time_in_force: "day" | "gtc";
  status: PaperIntentStatus;
  idempotency_key: string;
  created_at: string;
};

export type PaperRiskDecision = {
  decision_id: string;
  intent_id: string;
  result: "pass" | "reject";
  reason_codes: string[];
  explanation: string;
  estimated_notional: number;
  created_at: string;
};

export type PaperAuditEvent = {
  event_id: string;
  actor_type: string;
  resource_type: string;
  resource_id: string;
  action: string;
  outcome: string;
  reason_code: string;
  message: string;
  created_at: string;
};

export type PaperIntentResponse = {
  scope: "paper_only";
  replayed: boolean;
  intent: PaperIntent;
  latest_risk_decision: PaperRiskDecision | null;
  audit_events: PaperAuditEvent[];
};
```

- [ ] **Step 2: Add paper trading API methods**

After `listStrategyExperimentCandidates`, add:

```ts
export function listPaperAccounts(): Promise<PaperAccountListResponse> {
  return requestJson<PaperAccountListResponse>("/api/paper-trading/accounts");
}

export function createPaperAccount(): Promise<PaperAccountResponse> {
  return requestJson<PaperAccountResponse>("/api/paper-trading/accounts", {
    method: "POST",
    body: JSON.stringify({
      name: "Default paper account",
      base_currency: "USD",
      starting_cash: 100_000,
    }),
  });
}

export function createPaperIntentDraft(payload: {
  accountId: string;
  candidateId: string;
  symbol: string;
  assetClass: PaperIntent["asset_class"];
}): Promise<PaperIntentResponse> {
  return requestJson<PaperIntentResponse>("/api/paper-trading/intents", {
    method: "POST",
    headers: { "Idempotency-Key": `candidate-paper-${payload.candidateId}` },
    body: JSON.stringify({
      account_id: payload.accountId,
      source_reference_id: payload.candidateId,
      symbol: payload.symbol,
      asset_class: payload.assetClass,
      side: "buy",
      quantity: 1,
      order_type: "market",
      time_in_force: "day",
    }),
  });
}

export function runPaperIntentRiskCheck(intent: PaperIntent): Promise<PaperIntentResponse> {
  return requestJson<PaperIntentResponse>(`/api/paper-trading/intents/${intent.intent_id}/risk-check`, {
    method: "POST",
    body: JSON.stringify({
      allowed_symbols: [intent.symbol],
      allowed_asset_classes: [intent.asset_class],
      max_notional_per_intent: 2_000,
      max_daily_notional: 5_000,
      current_daily_notional: 0,
    }),
  });
}

export function reviewPaperIntent(intentId: string, decision: "approve" | "reject"): Promise<PaperIntentResponse> {
  return requestJson<PaperIntentResponse>(`/api/paper-trading/intents/${intentId}/review`, {
    method: "POST",
    body: JSON.stringify({
      decision,
      message: decision === "approve" ? "Approved from Strategy Lab paper review." : "Rejected from Strategy Lab paper review.",
    }),
  });
}

export function submitPaperIntent(intentId: string): Promise<PaperIntentResponse> {
  return requestJson<PaperIntentResponse>(`/api/paper-trading/intents/${intentId}/paper-submit`, {
    method: "POST",
    body: JSON.stringify({ market_price: 500 }),
  });
}

export function cancelPaperIntent(intentId: string): Promise<PaperIntentResponse> {
  return requestJson<PaperIntentResponse>(`/api/paper-trading/intents/${intentId}/cancel`, {
    method: "POST",
    body: JSON.stringify({ message: "Cancelled from Strategy Lab paper review." }),
  });
}
```

- [ ] **Step 3: Run frontend build and verify type errors for unused methods do not exist**

Run on Ubuntu temporary clone:

```bash
ssh yasin-ubuntu 'cd /tmp/<slice7-clone>/frontend && npm run build'
```

Expected: build may still fail because Strategy Lab UI does not use the new API yet if `noUnusedLocals` is enabled. If it fails for unused exports, proceed to Task 4 before rerunning.

## Task 4: Add Candidate-to-Paper UI State and Actions

**Files:**
- Modify: `frontend/src/features/strategy-lab/StrategyLabPanel.tsx`

- [ ] **Step 1: Add imports**

Add icons to the existing lucide import:

```ts
  ClipboardCheck,
  ShieldCheck,
```

Add API imports:

```ts
  cancelPaperIntent,
  createPaperAccount,
  createPaperIntentDraft,
  listPaperAccounts,
  reviewPaperIntent,
  runPaperIntentRiskCheck,
  submitPaperIntent,
  type PaperAccount,
  type PaperIntentResponse,
```

- [ ] **Step 2: Add paper UI state**

Inside `StrategyLabPanel`, after candidate sort state, add:

```ts
  const [paperAccounts, setPaperAccounts] = useState<PaperAccount[]>([]);
  const [paperIntent, setPaperIntent] = useState<PaperIntentResponse | null>(null);
  const [paperLoading, setPaperLoading] = useState(false);
  const [paperError, setPaperError] = useState<string | null>(null);
```

Add effect:

```ts
  useEffect(() => {
    void loadPaperAccounts();
  }, []);
```

- [ ] **Step 3: Add paper action functions**

Add these functions after `setCandidateReviewStatus`:

```ts
  async function loadPaperAccounts() {
    setPaperError(null);
    try {
      const response = await listPaperAccounts();
      setPaperAccounts(response.accounts);
    } catch (caught) {
      setPaperError(caught instanceof Error ? caught.message : "Paper accounts failed to load.");
    }
  }

  async function ensurePaperAccount(): Promise<PaperAccount> {
    const existing = paperAccounts.find((account) => account.status === "active");
    if (existing) return existing;
    const created = await createPaperAccount();
    setPaperAccounts([created.account]);
    return created.account;
  }

  async function createPaperDraftFromCandidate(candidate: StrategyExperimentCandidate) {
    setPaperLoading(true);
    setPaperError(null);
    try {
      const account = await ensurePaperAccount();
      const response = await createPaperIntentDraft({
        accountId: account.account_id,
        candidateId: candidate.experiment_id,
        symbol: candidate.symbol,
        assetClass: ["SPY", "QQQ"].includes(candidate.symbol.toUpperCase()) ? "etf" : "equity",
      });
      setPaperIntent(response);
    } catch (caught) {
      setPaperError(caught instanceof Error ? caught.message : "Paper draft creation failed.");
    } finally {
      setPaperLoading(false);
    }
  }

  async function runSelectedPaperRiskCheck() {
    if (!paperIntent) return;
    setPaperLoading(true);
    setPaperError(null);
    try {
      setPaperIntent(await runPaperIntentRiskCheck(paperIntent.intent));
    } catch (caught) {
      setPaperError(caught instanceof Error ? caught.message : "Paper RiskGuard check failed.");
    } finally {
      setPaperLoading(false);
    }
  }

  async function reviewSelectedPaperIntent(decision: "approve" | "reject") {
    if (!paperIntent) return;
    setPaperLoading(true);
    setPaperError(null);
    try {
      setPaperIntent(await reviewPaperIntent(paperIntent.intent.intent_id, decision));
    } catch (caught) {
      setPaperError(caught instanceof Error ? caught.message : "Paper review update failed.");
    } finally {
      setPaperLoading(false);
    }
  }

  async function submitSelectedPaperIntent() {
    if (!paperIntent) return;
    setPaperLoading(true);
    setPaperError(null);
    try {
      setPaperIntent(await submitPaperIntent(paperIntent.intent.intent_id));
    } catch (caught) {
      setPaperError(caught instanceof Error ? caught.message : "Paper simulation submit failed.");
    } finally {
      setPaperLoading(false);
    }
  }

  async function cancelSelectedPaperIntent() {
    if (!paperIntent) return;
    setPaperLoading(true);
    setPaperError(null);
    try {
      setPaperIntent(await cancelPaperIntent(paperIntent.intent.intent_id));
    } catch (caught) {
      setPaperError(caught instanceof Error ? caught.message : "Paper cancellation failed.");
    } finally {
      setPaperLoading(false);
    }
  }
```

- [ ] **Step 4: Wire candidate row action**

In the `CandidateBoardRow` call, add:

```tsx
onCreatePaperDraft={() => void createPaperDraftFromCandidate(candidate)}
paperLoading={paperLoading}
```

Update the `CandidateBoardRow` props:

```ts
  onCreatePaperDraft,
  paperLoading,
}: {
  candidate: StrategyExperimentCandidate;
  onOpen: () => void;
  onUseAsBase: () => void;
  onUseAsCandidate: () => void;
  onReject: () => void;
  onArchive: () => void;
  onCreatePaperDraft: () => void;
  paperLoading: boolean;
}) {
```

Add this button before reject/archive:

```tsx
          <Button
            type="button"
            size="sm"
            variant="outline"
            className="gap-2"
            disabled={paperLoading}
            onClick={onCreatePaperDraft}
          >
            <ClipboardCheck className="size-4" />
            Paper Draft
          </Button>
```

## Task 5: Add Paper Review Panel

**Files:**
- Modify: `frontend/src/features/strategy-lab/StrategyLabPanel.tsx`

- [ ] **Step 1: Add panel in Strategy Lab layout**

Add this card after the Candidate Review Board card:

```tsx
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <ShieldCheck className="size-4" />
            Paper Review
          </CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3">
          {paperError ? (
            <Alert variant="destructive">
              <AlertDescription>{paperError}</AlertDescription>
            </Alert>
          ) : null}
          {!paperIntent ? (
            <p className="text-sm text-muted-foreground">Select Paper Draft from a candidate experiment to start a paper-only review.</p>
          ) : (
            <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_320px]">
              <div className="rounded-md border p-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline">{paperIntent.scope}</Badge>
                  <Badge variant="secondary">{paperIntent.intent.status}</Badge>
                  <span className="text-sm font-medium">{paperIntent.intent.symbol}</span>
                </div>
                <div className="mt-3 grid gap-2 text-sm sm:grid-cols-2 lg:grid-cols-4">
                  <MetricTile label="Side" value={paperIntent.intent.side} compact />
                  <MetricTile label="Qty" value={String(paperIntent.intent.quantity)} compact />
                  <MetricTile label="Type" value={paperIntent.intent.order_type} compact />
                  <MetricTile label="TIF" value={paperIntent.intent.time_in_force} compact />
                </div>
                {paperIntent.latest_risk_decision ? (
                  <div className="mt-3 rounded-md bg-muted/30 p-3 text-sm">
                    <div className="font-medium">RiskGuard: {paperIntent.latest_risk_decision.result}</div>
                    <div className="mt-1 text-xs text-muted-foreground">
                      {paperIntent.latest_risk_decision.reason_codes.join(", ")}
                    </div>
                    <div className="mt-1 text-xs text-muted-foreground">
                      Estimated notional: {formatCurrency(paperIntent.latest_risk_decision.estimated_notional)}
                    </div>
                  </div>
                ) : null}
              </div>
              <div className="grid gap-2 content-start">
                <Button type="button" variant="outline" onClick={() => void runSelectedPaperRiskCheck()} disabled={paperLoading || paperIntent.intent.status === "paper_filled" || paperIntent.intent.status === "paper_cancelled"}>
                  Run RiskGuard
                </Button>
                <Button type="button" variant="outline" onClick={() => void reviewSelectedPaperIntent("approve")} disabled={paperLoading || paperIntent.latest_risk_decision?.result !== "pass"}>
                  Approve Paper
                </Button>
                <Button type="button" variant="outline" onClick={() => void reviewSelectedPaperIntent("reject")} disabled={paperLoading}>
                  Reject Paper
                </Button>
                <Button type="button" onClick={() => void submitSelectedPaperIntent()} disabled={paperLoading || paperIntent.intent.status !== "approved_for_paper"}>
                  Paper Submit
                </Button>
                <Button type="button" variant="outline" onClick={() => void cancelSelectedPaperIntent()} disabled={paperLoading || paperIntent.intent.status === "paper_filled" || paperIntent.intent.status === "paper_cancelled"}>
                  Cancel Paper
                </Button>
              </div>
            </div>
          )}
          {paperIntent ? (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Audit</TableHead>
                    <TableHead>Outcome</TableHead>
                    <TableHead>Message</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {paperIntent.audit_events.map((event) => (
                    <TableRow key={event.event_id}>
                      <TableCell>{event.reason_code}</TableCell>
                      <TableCell>{event.outcome}</TableCell>
                      <TableCell>{event.message}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : null}
        </CardContent>
      </Card>
```

- [ ] **Step 2: Run frontend build**

Run on Ubuntu:

```bash
ssh yasin-ubuntu 'cd /tmp/<slice7-clone>/frontend && npm run build'
```

Expected: PASS. If TypeScript errors occur, fix only the local type/import issues created by this slice.

## Task 6: Safety Grep and Regression

**Files:**
- No file changes.

- [ ] **Step 1: Run frontend/backend safety grep**

Run:

```bash
rg -n "broker|live execution|place_order|submit_order|ibkr|alpaca|order_id|account_number|requests\\.|httpx|aiohttp|MCP|agent scope|T scope|Buy|Sell|Live" frontend/src/features/strategy-lab/StrategyLabPanel.tsx frontend/src/lib/api.ts backend/app/paper_trading backend/tests/test_paper_trading_api.py
```

Expected: no output except enum values, user-facing `Side`, negative test assertions, and existing paper-only backend code. If visible UI copy implies live trading or broker execution, change it.

- [ ] **Step 2: Run backend focused paper tests**

```bash
ssh yasin-ubuntu 'cd /tmp/<slice7-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q tests/test_paper_trading_contracts.py tests/test_paper_trading_risk_guard.py tests/test_paper_trading_repository.py tests/test_paper_trading_api.py tests/test_paper_trading_adapter.py --tb=short'
```

Expected: PASS.

- [ ] **Step 3: Run backend full regression**

```bash
ssh yasin-ubuntu 'cd /tmp/<slice7-clone>/backend && PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest -q --tb=short'
```

Expected: PASS.

- [ ] **Step 4: Run frontend build**

```bash
ssh yasin-ubuntu 'cd /tmp/<slice7-clone>/frontend && npm run build'
```

Expected: PASS.

## Task 7: Update Documentation

**Files:**
- Modify: `docs/roadmap/phase-5-roadmap.md`
- Modify: `PROJECT.md`

- [ ] **Step 1: Update Slice 7 roadmap status**

Replace the Slice 7 section with:

```markdown
### Slice 7: Candidate-to-Paper UI

Status: implemented and validated on 2026-06-20.

Implemented:

- Candidate Review Board action to create a paper intent draft.
- Paper Review panel with intent status, RiskGuard result, audit timeline, and explicit human paper controls.
- Paper-only RiskGuard, approval/rejection, submit, and cancel actions.
- Minimal paper account bootstrap API for the Strategy Lab UI.
- UI copy uses paper simulation terminology and avoids broker/live trading language.

Implementation plan:

- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-5-slice-7-candidate-to-paper-ui.md`

Verification:

- Before committing the implementation, replace this verification list with the actual passing command outputs from Task 6.
- The implementation is not complete until backend account/API tests, focused paper tests, backend regression, frontend build, and safety grep all pass.
- Safety grep found no broker SDK, broker credentials, live order methods, network libraries, MCP trading tools, agent trading scope implementation, or live-trading UI copy.
```

- [ ] **Step 2: Update PROJECT status**

Update the current Phase 5 bullet in `PROJECT.md` to:

```markdown
- Current Phase 5 state: Phase 5 is in paper-only backend and UI implementation. Phase 4 completed the approved research-only Strategy Lab experiment workbench scope. Phase 5 now has paper-only architecture documentation, backend domain contracts, pure RiskGuard evaluator, SQLAlchemy persistence models, SQL schema, repository methods, append-only audit event persistence, human-facing paper intent API endpoints, a local deterministic paper adapter, and a Candidate-to-Paper Strategy Lab UI flow for paper draft creation, RiskGuard review, human approval/rejection, paper submit, and cancellation. Live broker execution, broker credentials, broker account mutation, AI-directed live trading, trading-scope MCP tools, network execution, live-trading UI controls, and automatic paper-to-live promotion remain out of scope.
```

## Task 8: Final Commit and Push

**Files:**
- Stage all files touched in this implementation.

- [ ] **Step 1: Run whitespace check**

```bash
git diff --check
```

Expected: no output.

- [ ] **Step 2: Stage files**

```bash
git add backend/app/paper_trading/repository.py backend/app/paper_trading/router.py backend/tests/test_paper_trading_api.py frontend/src/lib/api.ts frontend/src/features/strategy-lab/StrategyLabPanel.tsx docs/roadmap/phase-5-roadmap.md PROJECT.md
```

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: add candidate to paper ui flow"
```

- [ ] **Step 4: Push**

```bash
git push origin aquantlens-us
```

## Self-Review Checklist

- Spec coverage: Candidate Board creates paper drafts; Paper Review panel handles RiskGuard, approve/reject, submit, and cancel.
- Safety boundary: No broker credentials, broker routes, broker SDK calls, live execution, MCP trading tools, agent trading scope, or paper-to-live promotion.
- UI copy: Uses paper terminology; no buy/sell broker buttons or live-trading wording.
- Type consistency: Frontend paper types match backend response fields exactly.
- Verification: Backend tests and frontend build are required on Ubuntu before completion.
