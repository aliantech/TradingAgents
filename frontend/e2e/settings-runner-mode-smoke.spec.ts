import { expect, test, type Page, type Route } from "@playwright/test";

const now = "2026-06-20T12:00:00Z";

test("settings exposes persisted TradingAgents runner mode without provider calls", async ({ page }) => {
  await installApiMocks(page);

  await page.goto("/#settings");
  await page.getByRole("tab", { name: /模型与 Agent|Models and Agents/ }).click();

  await expect(page.getByText(/TradingAgents Runner 模式|TradingAgents Runner Mode/)).toBeVisible();
  await expect(page.getByText("deterministic").first()).toBeVisible();
  await page.getByRole("combobox").filter({ hasText: "deterministic" }).click();
  await expect(page.getByRole("option", { name: "real-tradingagents" })).toBeVisible();
  await expect(page.getByText(/默认 deterministic|Defaults to deterministic/)).toBeVisible();
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
      return json(route, { items: settingsItems() });
    }
    if (method === "GET" && pathname === "/api/reports") {
      return json(route, []);
    }
    if (method === "GET" && pathname === "/api/analysis/runs") {
      return json(route, { runs: [] });
    }
    if (method === "GET" && pathname === "/api/market-data/bars") {
      return json(route, { symbol: url.searchParams.get("symbol") ?? "SPY", timeframe: "1d", bars: [] });
    }
    if (method === "GET" && pathname === "/api/market-data/sync-runs") {
      return json(route, { runs: [] });
    }
    if (method === "GET" && pathname === "/api/market-data/sync-summary") {
      return json(route, syncSummary());
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

function settingsItems() {
  return [
    setting("AQUANTLENS_TRADINGAGENTS_RUNNER_MODE", "deterministic"),
    setting("AQUANTLENS_TRADINGAGENTS_LLM_PROVIDER", "openai"),
    setting("AQUANTLENS_TRADINGAGENTS_QUICK_THINK_LLM", "gpt-5.4-mini"),
    setting("AQUANTLENS_TRADINGAGENTS_DEEP_THINK_LLM", "gpt-5.5"),
    setting("AQUANTLENS_TRADINGAGENTS_OUTPUT_LANGUAGE", "Chinese"),
    setting("AQUANTLENS_TRADINGAGENTS_SELECTED_ANALYSTS", "market,news,fundamentals"),
    setting("AQUANTLENS_TRADINGAGENTS_MAX_DEBATE_ROUNDS", "1"),
    setting("AQUANTLENS_TRADINGAGENTS_MAX_RISK_DISCUSS_ROUNDS", "1"),
  ];
}

function setting(key: string, value: string) {
  return {
    key,
    value,
    category: "model",
    is_secret: false,
    has_value: true,
    updated_at: now,
  };
}

function syncSummary() {
  return {
    total_runs: 0,
    succeeded: 0,
    failed: 0,
    rows_written: 0,
    latest_status: null,
    latest_finished_at: null,
    average_duration_ms: 0,
  };
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
