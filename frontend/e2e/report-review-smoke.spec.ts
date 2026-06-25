import { expect, test, type Page, type Route } from "@playwright/test";

const analysisId = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
const reportId = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb";
const reviewId = "dddddddd-dddd-4ddd-8ddd-dddddddddddd";
const now = "2026-06-20T12:00:00Z";

test("report review is visible from reports and runs", async ({ page }) => {
  await installApiMocks(page);

  await page.goto("/#reports");
  await page.getByRole("button", { name: /SPY 中文报告|SPY Chinese Report/ }).click();
  await expect(page.getByText(/待评审|Needs Review/).first()).toBeVisible();

  await page.getByLabel(/备注|Notes/).fill("结构清楚，研究边界明确。");
  await page.getByRole("button", { name: /保存评审|Save Review/ }).click();

  await expect(page.getByText(/已评审|Reviewed/).first()).toBeVisible();
  await expect(page.getByText("结构清楚，研究边界明确。").first()).toBeVisible();

  await page.goto("/#runs");
  await page.getByRole("button", { name: /进度|Progress/ }).click();

  await expect(page.getByText(/报告评审状态|Report Review Status/)).toBeVisible();
  await expect(page.getByText("结构清楚，研究边界明确。").first()).toBeVisible();
});

async function installApiMocks(page: Page) {
  const reviews: unknown[] = [];

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
    if (method === "GET" && pathname === "/api/analysis/runs") {
      return json(route, { runs: [completedRun()] });
    }
    if (method === "GET" && pathname === `/api/analysis/${analysisId}`) {
      return json(route, completedStatus());
    }
    if (method === "GET" && pathname === "/api/reports") {
      return json(route, [reportListItem()]);
    }
    if (method === "GET" && pathname === `/api/reports/${reportId}`) {
      return json(route, report());
    }
    if (method === "GET" && pathname === `/api/reports/${reportId}/comparison`) {
      return json(route, { detail: "previous report not found" }, 404);
    }
    if (method === "GET" && pathname === `/api/reports/${reportId}/reviews`) {
      return json(route, reviews);
    }
    if (method === "POST" && pathname === `/api/reports/${reportId}/reviews`) {
      const payload = route.request().postDataJSON();
      const review = {
        ...payload,
        review_id: reviewId,
        report_id: reportId,
        created_at: now,
      };
      reviews.unshift(review);
      return json(route, review, 201);
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

function completedStatus() {
  return {
    analysis_id: analysisId,
    symbol: "SPY",
    asset_type: "etf",
    status: "completed",
    language: "zh",
    report_id: reportId,
    progress: [
      { step: "queued", status: "completed", message: "SPY analysis queued." },
      { step: "tradingagents", status: "completed", message: "TradingAgents fixture completed." },
      { step: "report", status: "completed", message: "Chinese report persisted." },
    ],
  };
}

function completedRun() {
  return {
    analysis_id: analysisId,
    symbol: "SPY",
    asset_type: "etf",
    status: "completed",
    language: "zh",
    analysis_date: "2026-06-20",
    llm_provider: "openai",
    model: "gpt-5.5",
    depth: "standard",
    analyst_set: "macro-options",
    research_template: "general",
    created_at: now,
    updated_at: now,
    report_id: reportId,
    failure_diagnostic: null,
  };
}

function reportListItem() {
  return {
    report_id: reportId,
    analysis_id: analysisId,
    symbol: "SPY",
    language: "zh",
    analyst_set: "macro-options",
    research_template: "general",
    summary: "SPY 中文 AI 投研摘要",
    confidence: 0.61,
  };
}

function report() {
  return {
    ...reportListItem(),
    market_background: "市场背景",
    fundamental_analysis: "基本面",
    technical_analysis: "技术面",
    sentiment_analysis: "情绪面",
    options_observation: "期权观察",
    bull_case: "多头情景",
    bear_case: "空头情景",
    risk_factors: ["宏观事件"],
    evidence_labels: ["deterministic-tradingagents-fixture"],
    trade_plan: "研究计划",
    position_sizing: "研究阶段不生成实盘仓位。",
    take_profit_stop_loss: "风控参考",
    markdown: "# SPY AI 投研报告",
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
