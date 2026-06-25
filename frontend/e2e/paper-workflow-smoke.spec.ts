import { expect, test, type Page, type Route } from "@playwright/test";

const now = "2026-06-20T12:00:00Z";
const accountId = "11111111-1111-4111-8111-111111111111";
const candidateId = "22222222-2222-4222-8222-222222222222";
const intentId = "33333333-3333-4333-8333-333333333333";

test("Strategy Lab paper workflow stays paper-only", async ({ page }) => {
  await installApiMocks(page);

  await page.goto("/#strategy");

  await expect(page.getByText("Candidate Review Board")).toBeVisible();
  await expect(page.getByText("Paper Review")).toBeVisible();
  await expect(page.getByText("Select Paper Draft from a candidate experiment to start a paper-only review.")).toBeVisible();

  await page.getByRole("button", { name: "Paper Draft" }).click();
  await expect(page.getByText("paper_only").first()).toBeVisible();
  await expect(page.getByText("Draft", { exact: true }).last()).toBeVisible();
  await expect(page.getByText("SPY").first()).toBeVisible();

  await page.getByRole("button", { name: "Run RiskGuard" }).click();
  await expect(page.getByText("RiskGuard: pass")).toBeVisible();
  await expect(page.getByText("Estimated notional:")).toBeVisible();

  await page.getByRole("button", { name: "Approve Paper" }).click();
  await expect(page.getByText("Approved for paper", { exact: true }).last()).toBeVisible();

  await page.getByRole("button", { name: "Paper Submit" }).click();
  await expect(page.getByText("Paper filled", { exact: true }).last()).toBeVisible();
  await expect(page.getByText("paper_fill_created", { exact: true }).last()).toBeVisible();
  await expect(page.getByText("Paper Risk Dashboard")).toBeVisible();
  await expect(page.getByText("Equity", { exact: true })).toBeVisible();
  await expect(page.getByText("$100,013")).toBeVisible();

  await expect(page.getByText(/live trading/i)).toHaveCount(0);
  await expect(page.getByText(/does not connect to a broker/i)).toBeVisible();
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
      return json(route, { items: [] });
    }
    if (method === "GET" && pathname === "/api/reports") {
      return json(route, []);
    }
    if (method === "GET" && pathname === "/api/analysis/runs") {
      return json(route, { runs: [] });
    }
    if (method === "GET" && pathname === "/api/market-data/bars") {
      return json(route, { symbol: url.searchParams.get("symbol") ?? "SPY", timeframe: "1d", bars: marketBars() });
    }
    if (method === "GET" && pathname === "/api/market-data/sync-runs") {
      return json(route, { runs: [] });
    }
    if (method === "GET" && pathname === "/api/market-data/sync-summary") {
      return json(route, {
        total_runs: 0,
        succeeded: 0,
        failed: 0,
        rows_written: 0,
        latest_status: null,
        latest_finished_at: null,
        average_duration_ms: 0,
      });
    }
    if (method === "GET" && pathname === "/api/market-data/sync-summary/groups") {
      return json(route, { groups: [] });
    }
    if (method === "GET" && pathname === "/api/market-data/sync-health") {
      return json(route, syncHealth());
    }
    if (method === "GET" && pathname === "/api/market-data/provider-readiness") {
      return json(route, { provider: "finance_data_hub", ready: true, missing: [], message: "Ready" });
    }
    if (method === "GET" && pathname === "/api/options/contracts") {
      return json(route, { underlying_symbol: url.searchParams.get("underlying") ?? "SPY", expiry: null, contracts: [] });
    }
    if (method === "GET" && pathname === "/api/options/chain") {
      return json(route, {
        underlying_symbol: url.searchParams.get("underlying") ?? "SPY",
        expiry: url.searchParams.get("expiry") ?? "2026-06-26",
        snapshots: [],
      });
    }
    if (method === "GET" && pathname === "/api/strategy-lab/strategies") {
      return json(route, strategyCatalog());
    }
    if (method === "POST" && pathname === "/api/strategy-lab/signal-strategy/preview") {
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
    if (method === "GET" && pathname === `/api/paper-trading/accounts/${accountId}/summary`) {
      return json(route, paperAccountSummary());
    }
    if (method === "POST" && pathname === `/api/paper-trading/accounts/${accountId}/pnl-snapshot`) {
      return json(route, paperPnlSnapshot());
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
    provider: "finance_data_hub",
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
    volume: 1_000_000 + index,
    source: "mock",
  }));
}

function strategyCatalog() {
  return {
    scope: "research_only",
    strategies: [
      {
        strategy_id: "ma-cross-research",
        name: "MA Cross Research",
        description: "Moving average research preview.",
        scope: "research_only",
        default_parameters: { fast_window: 2, slow_window: 3 },
        parameter_schema: {},
      },
    ],
  };
}

function strategyPreview() {
  return {
    scope: "research_only",
    strategy: {
      strategy_id: "ma-cross-research",
      name: "MA Cross Research",
      description: "Moving average research preview.",
      parameters: { fast_window: 2, slow_window: 3 },
    },
    signals: [],
    backtest: {
      mode: "research_only",
      initial_equity: 10000,
      final_equity: 10120,
      return_pct: 1.2,
      max_drawdown_pct: -0.4,
      trade_count: 2,
      trades: [],
      equity_curve: [],
    },
    overlay: {
      symbol: "SPY",
      price_series: marketBars().map((bar) => ({ time: bar.timestamp.slice(0, 10), value: bar.close })),
      markers: [],
    },
    note: null,
  };
}

function strategyCandidates() {
  return {
    scope: "research_only",
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
        signal_count: 2,
        review_checklist: {
          hypothesis_clear: true,
          risk_reviewed: true,
          report_linked: true,
        },
        tags: ["candidate"],
        created_at: now,
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

function paperAccountSummary() {
  return {
    scope: "paper_only",
    account: paperAccount(),
    positions: [
      {
        position_id: "55555555-5555-4555-8555-555555555555",
        account_id: accountId,
        symbol: "SPY",
        asset_class: "etf",
        quantity: 1,
        average_price: 500,
        updated_at: now,
      },
    ],
    recent_intents: [paperIntentResponse("paper_filled", riskDecision(), []).intent],
    recent_fills: [
      {
        fill_id: "66666666-6666-4666-8666-666666666666",
        intent_id: intentId,
        account_id: accountId,
        symbol: "SPY",
        asset_class: "etf",
        side: "buy",
        quantity: 1,
        fill_price: 500,
        filled_at: now,
      },
    ],
    recent_audit_events: paperIntentResponse("paper_filled", riskDecision(), ["paper_fill_created"]).audit_events,
  };
}

function paperPnlSnapshot() {
  return {
    scope: "paper_only",
    snapshot: {
      account_id: accountId,
      base_currency: "USD",
      current_cash: 99500,
      as_of: now,
      price_state: "complete",
      total_market_value: 513,
      total_unrealized_pnl: 13,
      total_realized_pnl: 0,
      account_equity: 100013,
      positions: [
        {
          position_id: "55555555-5555-4555-8555-555555555555",
          account_id: accountId,
          symbol: "SPY",
          asset_class: "etf",
          quantity: 1,
          average_price: 500,
          multiplier: 1,
          price_state: "fresh",
          reference_price: 513,
          reference_priced_at: now,
          market_value: 513,
          cost_basis: 500,
          unrealized_pnl: 13,
        },
      ],
    },
  };
}

function paperIntentResponse(status: string, latestRiskDecision: unknown, actions: string[]) {
  return {
    scope: "paper_only",
    replayed: false,
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
      reason_code: action,
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
    explanation: "Paper RiskGuard passed.",
    estimated_notional: 502,
    created_at: now,
  };
}
