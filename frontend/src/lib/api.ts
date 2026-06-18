import { resolveApiBaseUrl } from "./apiBaseUrl";

export type AnalysisProgressEvent = {
  step: string;
  status: string;
  message: string;
};

export type BackendHealth = {
  service: string;
  status: string;
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

export type AnalysisStartPayload = {
  symbol: string;
  assetType: "equity" | "etf" | "index" | "option";
  analysisDate: string;
  language: "zh" | "en";
  llmProvider: string;
  model: string;
  depth: "quick" | "standard" | "deep";
  analystSet: string;
  researchTemplate: "general" | "earnings-preview" | "macro-options-readthrough" | "technical-setup";
};

export type AnalysisRunItem = {
  analysis_id: string;
  symbol: string;
  asset_type: string;
  status: string;
  language: string;
  analysis_date: string;
  llm_provider: string;
  model: string;
  depth: string;
  analyst_set: string;
  research_template: string;
  created_at: string;
  updated_at: string;
  report_id: string | null;
};

export type AnalysisRunsResponse = {
  runs: AnalysisRunItem[];
};

export type ReportListItem = {
  report_id: string;
  analysis_id: string;
  symbol: string;
  language: string;
  analyst_set: string;
  research_template: string;
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
  evidence_labels: string[];
  trade_plan: string;
  position_sizing: string;
  take_profit_stop_loss: string;
  markdown: string | null;
};

export type ReportComparisonSection = {
  current: string;
  previous: string;
  changed: boolean;
};

export type ReportComparison = {
  symbol: string;
  current: ReportListItem;
  previous: ReportListItem;
  confidence_delta: number;
  risk_factor_changes: {
    added: string[];
    removed: string[];
  };
  section_changes: Record<string, ReportComparisonSection>;
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

export type MarketTimeframe = "1m" | "5m" | "1d";

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

export type ProviderSyncHealth = {
  provider: string;
  sync_type: string;
  status: string;
  total_runs: number;
  failed_runs: number;
  failure_rate: number;
  latest_status: string | null;
  latest_finished_at: string | null;
  minutes_since_latest: number | null;
  stale_after_minutes: number;
  message: string;
};

export type ProviderReadiness = {
  provider: string;
  ready: boolean;
  missing: string[];
  message: string;
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

export type OptionBar = {
  option_symbol: string;
  timeframe: MarketTimeframe;
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  source: string;
};

export type OptionChainResponse = {
  underlying_symbol: string;
  expiry: string;
  snapshots: OptionSnapshot[];
};

export type OptionContract = {
  option_symbol: string;
  underlying_symbol: string;
  expiry: string;
  strike: number;
  option_type: string;
  exercise_style: string | null;
  expiration_type: string | null;
  source: string;
};

export type OptionContractsResponse = {
  underlying_symbol: string;
  expiry: string | null;
  contracts: OptionContract[];
};

export type OptionBarsResponse = {
  option_symbol: string;
  timeframe: MarketTimeframe;
  bars: OptionBar[];
};

export type OptionChainSyncResponse = {
  provider: string;
  underlying_symbol: string;
  expiry: string;
  status: string;
  rows_written: number;
  error_message: string | null;
};

export type SettingItem = {
  key: string;
  value: string | null;
  category: string;
  is_secret: boolean;
  has_value: boolean;
  updated_at: string;
};

export type SettingsResponse = {
  items: SettingItem[];
};

export type SettingsUpsertItem = {
  key: string;
  value: string;
  category: string;
  is_secret: boolean;
};

export type StrategySignalRow = {
  timestamp: string;
  symbol: string;
  close: number;
  signal: number;
  position: number;
  reason: string;
};

export type StrategyBacktestResult = {
  mode: "research_only";
  initial_equity: number;
  final_equity: number;
  return_pct: number;
  trades: Array<{
    entry_timestamp: string;
    exit_timestamp: string;
    symbol: string;
    entry_price: number;
    exit_price: number;
    quantity: number;
    pnl: number;
  }>;
};

export type StrategyChartOverlay = {
  symbol: string;
  price_series: Array<{ time: string; value: number }>;
  markers: Array<{
    time: string;
    position: "belowBar" | "aboveBar";
    color: string;
    shape: "arrowUp" | "arrowDown";
    text: string;
  }>;
};

export type StrategyPreviewResponse = {
  strategy: {
    strategy_id: string;
    name: string;
    description: string;
    parameters: {
      fast_window: number;
      slow_window: number;
    };
  };
  signals: StrategySignalRow[];
  backtest: StrategyBacktestResult;
  overlay: StrategyChartOverlay;
  note: Record<string, unknown> | null;
  scope: "research_only";
};

export type StrategyPreviewPayload = {
  symbol: string;
  fastWindow: number;
  slowWindow: number;
  initialEquity: number;
  bars: MarketBar[];
  reportId?: string | null;
};

export type StrategyExperiment = {
  experiment_id: string;
  title: string;
  symbol: string;
  strategy_id: string;
  scope: "research_only";
  parameters: {
    fast_window?: number;
    slow_window?: number;
    [key: string]: unknown;
  };
  preview: StrategyPreviewResponse;
  report_id: string | null;
  created_at: string;
  updated_at: string;
};

export type StrategyExperimentListResponse = {
  experiments: StrategyExperiment[];
};

export type StrategyExperimentCreatePayload = {
  title: string;
  symbol: string;
  strategyId: string;
  parameters: StrategyExperiment["parameters"];
  preview: StrategyPreviewResponse;
  reportId?: string | null;
};

export type StrategyExperimentComparisonMetric = {
  experiment_id: string;
  title: string;
  final_equity: number;
  return_pct: number;
  trade_count: number;
  marker_count: number;
  signal_count: number;
  parameters: StrategyExperiment["parameters"];
};

export type StrategyExperimentComparison = {
  scope: "research_only";
  symbol: string;
  base: StrategyExperimentComparisonMetric;
  candidate: StrategyExperimentComparisonMetric;
  deltas: {
    final_equity: number;
    return_pct: number;
    trade_count: number;
    marker_count: number;
    signal_count: number;
  };
  parameter_deltas: Record<string, { base: unknown; candidate: unknown; changed: boolean }>;
};

const API_BASE_URL = resolveApiBaseUrl({
  configuredBaseUrl: import.meta.env.VITE_API_BASE_URL,
  pageHostname: globalThis.location?.hostname,
});

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

  const contentType = response.headers.get("content-type") ?? "";
  if (!contentType.toLowerCase().includes("application/json")) {
    throw new Error(`API response was not JSON for ${path}`);
  }

  try {
    return (await response.json()) as T;
  } catch {
    throw new Error(`API response JSON parse failed for ${path}`);
  }
}

export async function startAnalysis(payload: AnalysisStartPayload): Promise<AnalysisStatus> {
  const queued = await requestJson<{ analysis_id: string }>("/api/analysis", {
    method: "POST",
    body: JSON.stringify({
      symbol: payload.symbol,
      asset_type: payload.assetType,
      analysis_date: payload.analysisDate,
      language: payload.language,
      llm_provider: payload.llmProvider,
      model: payload.model,
      depth: payload.depth,
      analyst_set: payload.analystSet,
      research_template: payload.researchTemplate,
    }),
  });

  return requestJson<AnalysisStatus>(`/api/analysis/${queued.analysis_id}`);
}

export function listReports(): Promise<ReportListItem[]> {
  return requestJson<ReportListItem[]>("/api/reports");
}

export function getBackendHealth(): Promise<BackendHealth> {
  return requestJson<BackendHealth>("/api/health");
}

export function listAnalysisRuns(): Promise<AnalysisRunsResponse> {
  return requestJson<AnalysisRunsResponse>("/api/analysis/runs");
}

export function getAnalysisStatus(analysisId: string): Promise<AnalysisStatus> {
  return requestJson<AnalysisStatus>(`/api/analysis/${analysisId}`);
}

export async function retryAnalysis(analysisId: string): Promise<AnalysisStatus> {
  const queued = await requestJson<{ analysis_id: string }>(`/api/analysis/${analysisId}/retry`, {
    method: "POST",
  });
  return requestJson<AnalysisStatus>(`/api/analysis/${queued.analysis_id}`);
}

export function getReport(reportId: string): Promise<ResearchReport> {
  return requestJson<ResearchReport>(`/api/reports/${reportId}`);
}

export function getReportComparison(reportId: string): Promise<ReportComparison> {
  return requestJson<ReportComparison>(`/api/reports/${reportId}/comparison`);
}

export function getMarketBars(symbol: string, timeframe: MarketTimeframe = "1m"): Promise<MarketBarsResponse> {
  const params = new URLSearchParams({ symbol, timeframe });
  return requestJson<MarketBarsResponse>(`/api/market-data/bars?${params.toString()}`);
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

export function getProviderSyncHealth(filters: ProviderSyncFilters = {}): Promise<ProviderSyncHealth> {
  return requestJson<ProviderSyncHealth>(`/api/market-data/sync-health${providerSyncQuery(filters)}`);
}

export function getProviderReadiness(provider: string): Promise<ProviderReadiness> {
  const params = new URLSearchParams({ provider });
  return requestJson<ProviderReadiness>(`/api/market-data/provider-readiness?${params.toString()}`);
}

export function syncDailyBars(symbol: string): Promise<DailyBarSyncResponse> {
  return requestJson<DailyBarSyncResponse>("/api/market-data/sync-daily-bars", {
    method: "POST",
    body: JSON.stringify({
      symbol,
      start: "2026-06-16",
      end: "2026-06-17",
    }),
  });
}

export function getOptionChain(underlying: string, expiry = "2026-06-17"): Promise<OptionChainResponse> {
  return requestJson<OptionChainResponse>(
    `/api/options/chain?underlying=${encodeURIComponent(underlying)}&expiry=${encodeURIComponent(expiry)}`,
  );
}

export function listOptionContracts(underlying: string, expiry?: string): Promise<OptionContractsResponse> {
  const params = new URLSearchParams({ underlying });
  if (expiry) {
    params.set("expiry", expiry);
  }
  return requestJson<OptionContractsResponse>(`/api/options/contracts?${params.toString()}`);
}

export function getOptionBars(optionSymbol: string, timeframe: MarketTimeframe = "1m"): Promise<OptionBarsResponse> {
  const params = new URLSearchParams({ option_symbol: optionSymbol, timeframe });
  return requestJson<OptionBarsResponse>(`/api/options/bars?${params.toString()}`);
}

export function syncOptionChain(
  underlying: string,
  expiry: string,
  provider = "polygon",
): Promise<OptionChainSyncResponse> {
  return requestJson<OptionChainSyncResponse>("/api/options/sync-chain", {
    method: "POST",
    body: JSON.stringify({
      underlying_symbol: underlying,
      expiry,
      provider,
      limit: 250,
    }),
  });
}

export function listSettings(): Promise<SettingsResponse> {
  return requestJson<SettingsResponse>("/api/settings");
}

export function upsertSettings(items: SettingsUpsertItem[]): Promise<SettingsResponse> {
  return requestJson<SettingsResponse>("/api/settings", {
    method: "PUT",
    body: JSON.stringify({ items }),
  });
}

export function previewSignalStrategy(payload: StrategyPreviewPayload): Promise<StrategyPreviewResponse> {
  return requestJson<StrategyPreviewResponse>("/api/strategy-lab/signal-strategy/preview", {
    method: "POST",
    body: JSON.stringify({
      symbol: payload.symbol,
      fast_window: payload.fastWindow,
      slow_window: payload.slowWindow,
      initial_equity: payload.initialEquity,
      bars: payload.bars.map((bar) => ({
        timestamp: bar.timestamp,
        symbol: bar.symbol,
        open: bar.open,
        high: bar.high,
        low: bar.low,
        close: bar.close,
        volume: bar.volume,
      })),
      report_id: payload.reportId,
    }),
  });
}

export function saveStrategyExperiment(payload: StrategyExperimentCreatePayload): Promise<StrategyExperiment> {
  return requestJson<StrategyExperiment>("/api/strategy-lab/experiments", {
    method: "POST",
    body: JSON.stringify({
      title: payload.title,
      symbol: payload.symbol,
      strategy_id: payload.strategyId,
      parameters: payload.parameters,
      preview: payload.preview,
      report_id: payload.reportId ?? null,
    }),
  });
}

export function listStrategyExperiments(symbol?: string): Promise<StrategyExperimentListResponse> {
  const params = new URLSearchParams();
  if (symbol) {
    params.set("symbol", symbol);
  }
  const query = params.toString();
  return requestJson<StrategyExperimentListResponse>(`/api/strategy-lab/experiments${query ? `?${query}` : ""}`);
}

export function getStrategyExperiment(experimentId: string): Promise<StrategyExperiment> {
  return requestJson<StrategyExperiment>(`/api/strategy-lab/experiments/${experimentId}`);
}

export function duplicateStrategyExperiment(experimentId: string): Promise<StrategyExperiment> {
  return requestJson<StrategyExperiment>(`/api/strategy-lab/experiments/${experimentId}/duplicate`, {
    method: "POST",
  });
}

export function compareStrategyExperiments(
  baseExperimentId: string,
  candidateExperimentId: string,
): Promise<StrategyExperimentComparison> {
  const params = new URLSearchParams({
    base_id: baseExperimentId,
    candidate_id: candidateExperimentId,
  });
  return requestJson<StrategyExperimentComparison>(`/api/strategy-lab/experiments/compare?${params.toString()}`);
}
