# Phase 6 Slice 2 Paper Workflow Browser Smoke Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a minimal browser smoke test for the Strategy Lab Candidate-to-Paper workflow that proves the UI remains paper-only and can complete the draft, RiskGuard, approval, submit, and cancel controls against controlled API mocks.

**Architecture:** Add Playwright as a frontend dev dependency, keep the smoke test inside `frontend/e2e`, and intercept API calls in the browser test instead of relying on a live backend or seeded database. The test exercises the real Vite-built React app and only mocks same-origin app API responses.

**Tech Stack:** React/Vite/TypeScript frontend, Playwright Chromium browser test, npm scripts, mocked same-origin API routes.

---

## File Structure

- Modify: `frontend/package.json`
  - Add `e2e:paper` script.
  - Add `@playwright/test` dev dependency through `npm install -D`.
- Create: `frontend/playwright.config.ts`
  - Define Vite preview web server for the built app.
  - Set Chromium-only project for a small first smoke.
- Create: `frontend/e2e/paper-workflow-smoke.spec.ts`
  - Mock backend API responses required by app bootstrap and Strategy Lab.
  - Navigate to `/#strategy`.
  - Click Candidate Review Board `Paper Draft`.
  - Run RiskGuard.
  - Approve paper intent.
  - Submit to paper simulation.
  - Verify paper-only copy and absence of live-trading controls.
- Modify: `docs/roadmap/phase-6-roadmap.md`
  - Add the Slice 2 implementation plan reference while keeping Slice 2 planned until implemented.
- Modify: `PROJECT.md`
  - Add the Slice 2 implementation plan to Key Documents.
- Modify: `/Users/yasin/Documents/Yasin AI OS/04-Projects/aquantlens/LOG.md`
  - Record that Slice 2 is planned only.

## Assumptions

- The app can render Strategy Lab at `/#strategy` through the existing hash router.
- The smoke test should not require live backend services, database state, broker connectivity, or credentials.
- Playwright browser installation should happen on Ubuntu during implementation, not on Mac.
- The first smoke should cover one happy path with controlled API mocks; broader UI coverage belongs to later hardening.

## Safety Boundary

This slice must not add:

- Broker SDKs.
- Broker credentials.
- Live order methods.
- Trading-scope MCP tools.
- Live-trading UI controls.
- Paper-to-live promotion.
- Network execution from the paper adapter.

The test is allowed to intercept same-origin `/api/...` requests inside Playwright.

### Task 1: Add Playwright Script and Dependency

**Files:**
- Modify: `frontend/package.json`
- Generate: `frontend/package-lock.json` if npm updates it

- [ ] **Step 1: Install Playwright test dependency on Ubuntu**

Run:

```bash
ssh yasin-ubuntu 'cd /tmp/tradingagents-phase6-slice2/frontend && npm install -D @playwright/test'
```

Expected: `frontend/package.json` and `frontend/package-lock.json` include `@playwright/test`.

- [ ] **Step 2: Install Chromium browser on Ubuntu**

Run:

```bash
ssh yasin-ubuntu 'cd /tmp/tradingagents-phase6-slice2/frontend && npx playwright install chromium'
```

Expected: Chromium browser dependencies are available for Playwright smoke verification.

- [ ] **Step 3: Add npm script**

Modify `frontend/package.json` scripts to include:

```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview",
    "e2e:paper": "playwright test --config playwright.config.ts"
  }
}
```

- [ ] **Step 4: Verify script is discoverable**

Run:

```bash
ssh yasin-ubuntu 'cd /tmp/tradingagents-phase6-slice2/frontend && npm run'
```

Expected: output lists `e2e:paper`.

### Task 2: Add Playwright Configuration

**Files:**
- Create: `frontend/playwright.config.ts`

- [ ] **Step 1: Create config**

Create `frontend/playwright.config.ts`:

```ts
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: {
    timeout: 5_000,
  },
  fullyParallel: false,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:4173",
    trace: "retain-on-failure",
  },
  webServer: {
    command: "npm run build && npm run preview -- --host 127.0.0.1 --port 4173",
    url: "http://127.0.0.1:4173",
    reuseExistingServer: false,
    timeout: 120_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
```

- [ ] **Step 2: Run config smoke before test exists**

Run:

```bash
ssh yasin-ubuntu 'cd /tmp/tradingagents-phase6-slice2/frontend && npm run e2e:paper'
```

Expected: command starts the build and reports that no tests are found, or exits with the Playwright no-test status. This proves the config is loadable before adding the spec.

### Task 3: Add Paper Workflow Browser Smoke Spec

**Files:**
- Create: `frontend/e2e/paper-workflow-smoke.spec.ts`

- [ ] **Step 1: Create mocked browser smoke test**

Create `frontend/e2e/paper-workflow-smoke.spec.ts`:

```ts
import { expect, test, type Page, type Route } from "@playwright/test";

const now = "2026-06-20T12:00:00Z";
const accountId = "11111111-1111-4111-8111-111111111111";
const candidateId = "22222222-2222-4222-8222-222222222222";
const intentId = "33333333-3333-4333-8333-333333333333";

test("Strategy Lab paper workflow stays paper-only", async ({ page }) => {
  await installApiMocks(page);

  await page.goto("/#strategy");

  await expect(page.getByRole("heading", { name: "Candidate Review Board" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Paper Review" })).toBeVisible();
  await expect(page.getByText("Select Paper Draft from a candidate experiment to start a paper-only review.")).toBeVisible();

  await page.getByRole("button", { name: "Paper Draft" }).click();
  await expect(page.getByText("paper_only")).toBeVisible();
  await expect(page.getByText("draft")).toBeVisible();
  await expect(page.getByText("SPY")).toBeVisible();

  await page.getByRole("button", { name: "Run RiskGuard" }).click();
  await expect(page.getByText("RiskGuard: pass")).toBeVisible();
  await expect(page.getByText("Estimated notional:")).toBeVisible();

  await page.getByRole("button", { name: "Approve Paper" }).click();
  await expect(page.getByText("approved_for_paper")).toBeVisible();

  await page.getByRole("button", { name: "Paper Submit" }).click();
  await expect(page.getByText("paper_filled")).toBeVisible();
  await expect(page.getByText("paper_fill_created")).toBeVisible();

  await expect(page.getByText(/live/i)).toHaveCount(0);
  await expect(page.getByText(/broker/i)).toHaveCount(0);
  await expect(page.getByText(/paper-to-live/i)).toHaveCount(0);
});

async function installApiMocks(page: Page) {
  await page.route("**/api/**", async (route) => {
    const url = new URL(route.request().url());
    const method = route.request().method();
    const pathname = url.pathname;

    if (method === "GET" && pathname === "/api/health") {
      return json(route, { service: "AQuantLens API", status: "ok" });
    }
    if (method === "GET" && pathname === "/api/settings") {
      return json(route, { settings: [] });
    }
    if (method === "GET" && pathname === "/api/reports") {
      return json(route, { reports: [] });
    }
    if (method === "GET" && pathname === "/api/analysis/runs") {
      return json(route, { runs: [] });
    }
    if (method === "GET" && pathname === "/api/market-data/bars") {
      return json(route, { symbol: url.searchParams.get("symbol") ?? "SPY", timeframe: "1d", bars: marketBars() });
    }
    if (method === "GET" && pathname === "/api/market-data/sync/runs") {
      return json(route, { runs: [] });
    }
    if (method === "GET" && pathname === "/api/market-data/sync/summary") {
      return json(route, { total_runs: 0, succeeded: 0, failed: 0, rows_written: 0, latest_status: null, latest_finished_at: null, average_duration_ms: 0 });
    }
    if (method === "GET" && pathname === "/api/market-data/sync/summary/groups") {
      return json(route, { groups: [] });
    }
    if (method === "GET" && pathname === "/api/market-data/sync/health") {
      return json(route, syncHealth());
    }
    if (method === "GET" && pathname === "/api/market-data/providers/readiness") {
      return json(route, { provider: "polygon", ready: true, missing: [], message: "Ready" });
    }
    if (method === "GET" && pathname === "/api/options/contracts") {
      return json(route, { underlying_symbol: url.searchParams.get("underlying") ?? "SPY", expiry: null, contracts: [] });
    }
    if (method === "GET" && pathname === "/api/options/chain") {
      return json(route, { underlying_symbol: url.searchParams.get("underlying") ?? "SPY", expiry: url.searchParams.get("expiry") ?? "2026-06-26", snapshots: [] });
    }
    if (method === "GET" && pathname === "/api/strategy-lab/catalog") {
      return json(route, strategyCatalog());
    }
    if (method === "POST" && pathname === "/api/strategy-lab/preview") {
      return json(route, strategyPreview());
    }
    if (method === "GET" && pathname === "/api/strategy-lab/experiments") {
      return json(route, { experiments: [] });
    }
    if (method === "GET" && pathname === "/api/strategy-lab/experiments/candidates") {
      return json(route, strategyCandidates());
    }
    if (method === "GET" && pathname === "/api/paper-trading/accounts") {
      return json(route, { scope: "paper_only", accounts: [paperAccount()] });
    }
    if (method === "POST" && pathname === "/api/paper-trading/intents") {
      return json(route, paperIntentResponse("draft", null, ["intent_created"]));
    }
    if (method === "POST" && pathname === `/api/paper-trading/intents/${intentId}/risk-check`) {
      return json(route, paperIntentResponse("awaiting_review", riskDecision(), ["intent_created", "risk_passed"]));
    }
    if (method === "POST" && pathname === `/api/paper-trading/intents/${intentId}/review`) {
      return json(route, paperIntentResponse("approved_for_paper", riskDecision(), ["intent_created", "risk_passed", "human_approved"]));
    }
    if (method === "POST" && pathname === `/api/paper-trading/intents/${intentId}/paper-submit`) {
      return json(route, paperIntentResponse("paper_filled", riskDecision(), ["intent_created", "risk_passed", "human_approved", "paper_fill_created"]));
    }

    return json(route, { detail: `Unhandled mocked route: ${method} ${pathname}` }, 404);
  });
}

async function json(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

function syncHealth() {
  return {
    provider: "polygon",
    sync_type: "daily_bars",
    status: "ok",
    total_runs: 0,
    failed_runs: 0,
    failure_rate: 0,
    latest_status: null,
    latest_finished_at: null,
    minutes_since_latest: null,
    stale_after_minutes: 1440,
    message: "Ready",
  };
}

function marketBars() {
  return Array.from({ length: 12 }, (_, index) => ({
    symbol: "SPY",
    timeframe: "1d",
    timestamp: `2026-06-${String(index + 1).padStart(2, "0")}T00:00:00Z`,
    open: 500 + index,
    high: 505 + index,
    low: 498 + index,
    close: 502 + index,
    volume: 1000000 + index,
    source: "mock",
  }));
}

function strategyCatalog() {
  return {
    strategies: [
      {
        strategy_id: "ma-cross-research",
        name: "MA Cross Research",
        description: "Moving average research preview.",
        default_parameters: { fast_window: 2, slow_window: 3 },
      },
    ],
  };
}

function strategyPreview() {
  return {
    scope: "research_only",
    symbol: "SPY",
    strategy: {
      strategy_id: "ma-cross-research",
      name: "MA Cross Research",
      parameters: { fast_window: 2, slow_window: 3 },
    },
    metrics: {
      initial_equity: 10000,
      final_equity: 10120,
      return_pct: 1.2,
      max_drawdown_pct: -0.4,
      trade_count: 2,
      win_rate_pct: 50,
    },
    equity_curve: [],
    markers: [],
    disclaimers: ["Research preview only."],
  };
}

function strategyCandidates() {
  return {
    candidates: [
      {
        experiment_id: candidateId,
        title: "SPY candidate paper smoke",
        symbol: "SPY",
        strategy_id: "ma-cross-research",
        return_pct: 1.2,
        final_equity: 10120,
        trade_count: 2,
        marker_count: 2,
        review_status: "candidate",
        review_checklist: {
          hypothesis_clear: true,
          risk_reviewed: true,
          report_linked: true,
        },
        tags: ["candidate"],
        created_at: now,
        updated_at: now,
      },
    ],
  };
}

function paperAccount() {
  return {
    account_id: accountId,
    name: "Default paper account",
    base_currency: "USD",
    starting_cash: 100000,
    current_cash: 100000,
    status: "active",
    created_at: now,
  };
}

function paperIntentResponse(status: string, latestRiskDecision: unknown, actions: string[]) {
  return {
    scope: "paper_only",
    intent: {
      intent_id: intentId,
      account_id: accountId,
      source: "human",
      source_reference_id: candidateId,
      symbol: "SPY",
      asset_class: "etf",
      side: "buy",
      quantity: 1,
      order_type: "market",
      limit_price: null,
      time_in_force: "day",
      status,
      idempotency_key: `candidate-paper-${candidateId}`,
      created_at: now,
    },
    latest_risk_decision: latestRiskDecision,
    audit_events: actions.map((action, index) => ({
      event_id: `${index + 1}0000000-0000-4000-8000-000000000000`,
      resource_type: "intent",
      resource_id: intentId,
      actor_type: "human",
      action,
      outcome: action === "risk_passed" ? "pass" : "success",
      reason_code: null,
      message: action,
      created_at: now,
    })),
  };
}

function riskDecision() {
  return {
    decision_id: "44444444-4444-4444-8444-444444444444",
    intent_id: intentId,
    result: "pass",
    reason_codes: ["passed"],
    message: "Paper RiskGuard passed.",
    estimated_notional: 502,
    created_at: now,
  };
}
```

- [ ] **Step 2: Run browser smoke and verify failure or pass**

Run:

```bash
ssh yasin-ubuntu 'cd /tmp/tradingagents-phase6-slice2/frontend && npm run e2e:paper'
```

Expected: If selectors need adjustment, Playwright fails with a selector or visibility error. Do not weaken the paper-only assertions; adjust selectors to match the real UI text.

- [ ] **Step 3: Stabilize selectors with existing UI copy only**

Allowed changes:

```ts
await expect(page.getByRole("heading", { name: "Candidate Review Board" })).toBeVisible();
await expect(page.getByRole("heading", { name: "Paper Review" })).toBeVisible();
await page.getByRole("button", { name: "Paper Draft" }).click();
await page.getByRole("button", { name: "Run RiskGuard" }).click();
await page.getByRole("button", { name: "Approve Paper" }).click();
await page.getByRole("button", { name: "Paper Submit" }).click();
```

Do not add live-trading copy, broker copy, or hidden test-only UI controls.

- [ ] **Step 4: Verify smoke passes**

Run:

```bash
ssh yasin-ubuntu 'cd /tmp/tradingagents-phase6-slice2/frontend && npm run e2e:paper'
```

Expected:

```text
1 passed
```

### Task 4: Update Documentation

**Files:**
- Modify: `docs/roadmap/phase-6-roadmap.md`
- Modify: `PROJECT.md`
- Modify: `/Users/yasin/Documents/Yasin AI OS/04-Projects/aquantlens/LOG.md`

- [ ] **Step 1: Update roadmap Slice 2 status**

In `docs/roadmap/phase-6-roadmap.md`, change Slice 2 status from:

```markdown
Status: planned.
```

To:

```markdown
Status: implementation plan added on 2026-06-20.
```

Add:

```markdown
Implementation plan:

- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-6-slice-2-paper-workflow-browser-smoke.md`
```

- [ ] **Step 2: Update PROJECT.md key documents**

Add:

```markdown
- `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-6-slice-2-paper-workflow-browser-smoke.md`
```

- [ ] **Step 3: Append Yasin Brain log entry**

Append:

```markdown
## 2026-06-20 — TradingAgents US/options Phase 6 Slice 2 Paper Workflow Browser Smoke implementation plan

- Continued Phase 6 for the separate TradingAgents-based AQuantLens US/options branch.
- Added docs/superpowers/plans/2026-06-20-aquantlens-us-phase-6-slice-2-paper-workflow-browser-smoke.md.
- Planned a minimal Playwright Chromium browser smoke for the Strategy Lab Candidate-to-Paper UI using controlled same-origin API mocks.
- Planned verification covers Paper Draft, RiskGuard, human approval, Paper Submit, paper-only copy, and absence of live/broker/paper-to-live controls.
- Slice 2 remains planning only; no frontend dependency, test file, backend code, broker integration, network execution, credential handling, or live execution was added in this planning step.
- No secrets were read, printed, copied, or recorded.
```

### Task 5: Final Verification and Commit

**Files:**
- Verify: `docs/superpowers/plans/2026-06-20-aquantlens-us-phase-6-slice-2-paper-workflow-browser-smoke.md`
- Verify: `docs/roadmap/phase-6-roadmap.md`
- Verify: `PROJECT.md`

- [ ] **Step 1: Placeholder scan**

Run:

```bash
rg -n "unresolved placeholder wording" docs/superpowers/plans/2026-06-20-aquantlens-us-phase-6-slice-2-paper-workflow-browser-smoke.md
```

Expected: no matches.

- [ ] **Step 2: Safety grep**

Run:

```bash
rg -n "broker SDK|broker cred""entials|live order|live exec""ution|paper-to-live|trading-scope MCP|cred""ential" PROJECT.md docs/roadmap/phase-6-roadmap.md docs/superpowers/plans/2026-06-20-aquantlens-us-phase-6-slice-2-paper-workflow-browser-smoke.md
```

Expected: matches only appear in safety-boundary, non-goal, or out-of-scope statements.

- [ ] **Step 3: Check repository status**

Run:

```bash
git status --short --branch
```

Expected: only `PROJECT.md`, `docs/roadmap/phase-6-roadmap.md`, and the Slice 2 plan are changed.

- [ ] **Step 4: Commit**

Run:

```bash
git add PROJECT.md docs/roadmap/phase-6-roadmap.md docs/superpowers/plans/2026-06-20-aquantlens-us-phase-6-slice-2-paper-workflow-browser-smoke.md
git commit -m "docs: plan phase 6 paper browser smoke"
```

Expected: commit succeeds with documentation changes only.

- [ ] **Step 5: Push**

Run:

```bash
git push origin aquantlens-us
```

Expected: push succeeds.

## Self-Review

- Spec coverage: the plan covers Playwright setup, mocked Strategy Lab paper browser workflow, paper-only assertions, documentation updates, verification, commit, and push.
- Placeholder scan: no unresolved placeholder wording or unspecified test steps remain.
- Type consistency: mock object fields match the current `frontend/src/lib/api.ts` paper account, paper intent, risk decision, audit event, strategy catalog, and candidate response shapes.
