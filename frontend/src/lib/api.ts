export type AnalysisProgressEvent = {
  step: string;
  status: string;
  message: string;
};

export type AnalysisStatus = {
  analysis_id: string;
  symbol: string;
  asset_type: string;
  status: string;
  language: string;
  progress: AnalysisProgressEvent[];
  report_id: string | null;
};

export type ReportListItem = {
  report_id: string;
  analysis_id: string;
  symbol: string;
  language: string;
  summary: string;
  confidence: number;
};

export type ResearchReport = ReportListItem & {
  market_background: string;
  fundamental_analysis: string;
  technical_analysis: string;
  sentiment_analysis: string;
  options_observation: string;
  bull_case: string;
  bear_case: string;
  risk_factors: string[];
  trade_plan: string;
  position_sizing: string;
  take_profit_stop_loss: string;
  markdown: string | null;
};

export type MarketBar = {
  symbol: string;
  timeframe: string;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  source: string;
};

export type MarketBarsResponse = {
  symbol: string;
  timeframe: string;
  bars: MarketBar[];
};

export type ProviderSyncRunItem = {
  id: string;
  provider: string;
  sync_type: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  rows_written: number;
  error_message: string | null;
};

export type ProviderSyncRunsResponse = {
  runs: ProviderSyncRunItem[];
};

export type ProviderSyncFilters = {
  provider?: string;
  syncType?: string;
  startedAfter?: string;
  startedBefore?: string;
};

export type ProviderSyncSummary = {
  total_runs: number;
  succeeded: number;
  failed: number;
  rows_written: number;
  latest_status: string | null;
  latest_finished_at: string | null;
  average_duration_ms: number;
};

export type ProviderSyncSummaryGroup = ProviderSyncSummary & {
  provider: string;
  sync_type: string;
};

export type ProviderSyncSummaryGroupsResponse = {
  groups: ProviderSyncSummaryGroup[];
};

export type DailyBarSyncResponse = {
  status: string;
  rows_written: number;
  error_message: string | null;
};

export type OptionSnapshot = {
  option_symbol: string;
  underlying_symbol: string;
  timestamp: string;
  bid: number | null;
  ask: number | null;
  last: number | null;
  volume: number;
  open_interest: number | null;
  implied_volatility: number | null;
  delta: number | null;
  gamma: number | null;
  theta: number | null;
  vega: number | null;
  source: string;
};

export type OptionChainResponse = {
  underlying_symbol: string;
  expiry: string;
  snapshots: OptionSnapshot[];
};

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
    ...init,
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}

export async function startAnalysis(symbol: string): Promise<AnalysisStatus> {
  const queued = await requestJson<{ analysis_id: string }>("/api/analysis", {
    method: "POST",
    body: JSON.stringify({
      symbol,
      asset_type: symbol.toUpperCase() === "SPX" ? "index" : "etf",
      analysis_date: "2026-06-17",
      language: "zh",
      llm_provider: "openai",
      model: "gpt-5.5",
      depth: "standard",
    }),
  });

  return requestJson<AnalysisStatus>(`/api/analysis/${queued.analysis_id}`);
}

export function listReports(): Promise<ReportListItem[]> {
  return requestJson<ReportListItem[]>("/api/reports");
}

export function getReport(reportId: string): Promise<ResearchReport> {
  return requestJson<ResearchReport>(`/api/reports/${reportId}`);
}

export function getMarketBars(symbol: string): Promise<MarketBarsResponse> {
  return requestJson<MarketBarsResponse>(`/api/market-data/bars?symbol=${encodeURIComponent(symbol)}&timeframe=1m`);
}

function providerSyncQuery(filters: ProviderSyncFilters = {}, includeLimit = false) {
  const params = new URLSearchParams();
  if (includeLimit) {
    params.set("limit", "20");
  }
  if (filters.provider) {
    params.set("provider", filters.provider);
  }
  if (filters.syncType) {
    params.set("sync_type", filters.syncType);
  }
  if (filters.startedAfter) {
    params.set("started_after", filters.startedAfter);
  }
  if (filters.startedBefore) {
    params.set("started_before", filters.startedBefore);
  }
  const query = params.toString();
  return query ? `?${query}` : "";
}

export function listProviderSyncRuns(filters: ProviderSyncFilters = {}): Promise<ProviderSyncRunsResponse> {
  return requestJson<ProviderSyncRunsResponse>(`/api/market-data/sync-runs${providerSyncQuery(filters, true)}`);
}

export function getProviderSyncSummary(filters: ProviderSyncFilters = {}): Promise<ProviderSyncSummary> {
  return requestJson<ProviderSyncSummary>(`/api/market-data/sync-summary${providerSyncQuery(filters)}`);
}

export function listProviderSyncSummaryGroups(
  filters: ProviderSyncFilters = {},
): Promise<ProviderSyncSummaryGroupsResponse> {
  return requestJson<ProviderSyncSummaryGroupsResponse>(`/api/market-data/sync-summary/groups${providerSyncQuery(filters)}`);
}

export function syncDailyBars(symbol: string): Promise<DailyBarSyncResponse> {
  return requestJson<DailyBarSyncResponse>("/api/market-data/sync-daily-bars", {
    method: "POST",
    body: JSON.stringify({
      symbol,
      start: "2026-06-16",
      end: "2026-06-17",
      provider: "sample",
    }),
  });
}

export function getOptionChain(underlying: string): Promise<OptionChainResponse> {
  return requestJson<OptionChainResponse>(
    `/api/options/chain?underlying=${encodeURIComponent(underlying)}&expiry=2026-06-17`,
  );
}
