import { resolveApiBaseUrl } from "./apiBaseUrl";

export type AnalysisProgressEvent = {
  step: string;
  status: string;
  message: string;
};

export type AnalysisFailureDiagnostic = {
  category: string;
  failed_step: string;
  message: string;
  retry_guidance: string;
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
  failure_diagnostic?: AnalysisFailureDiagnostic | null;
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
  failure_diagnostic?: AnalysisFailureDiagnostic | null;
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

export type ReportReviewPayload = {
  reviewer: string;
  evidence_clarity: number;
  consistency: number;
  risk_coverage: number;
  options_relevance: number;
  chinese_readability: number;
  research_only_safety: number;
  notes: string;
};

export type ReportReview = ReportReviewPayload & {
  review_id: string;
  report_id: string;
  created_at: string;
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
  target_symbol: string | null;
  target_expiry: string | null;
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
  strategyId?: string;
  fastWindow: number;
  slowWindow: number;
  initialEquity: number;
  bars: MarketBar[];
  reportId?: string | null;
};

export type StrategyCatalogItem = {
  strategy_id: string;
  name: string;
  description: string;
  scope: "research_only";
  default_parameters: {
    fast_window: number;
    slow_window: number;
    [key: string]: unknown;
  };
  parameter_schema: Record<string, Record<string, unknown>>;
};

export type StrategyCatalogResponse = {
  scope: "research_only";
  strategies: StrategyCatalogItem[];
};

export type StrategyExperimentReviewStatus = "draft" | "reviewed" | "candidate" | "rejected";

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
  tags: string[];
  notes: string | null;
  archived: boolean;
  review_status: StrategyExperimentReviewStatus;
  review_checklist: Record<string, boolean>;
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
  tags?: string[];
  notes?: string | null;
  reportId?: string | null;
};

export type StrategyExperimentUpdatePayload = {
  tags?: string[];
  notes?: string | null;
  archived?: boolean;
  review_status?: StrategyExperimentReviewStatus;
  review_checklist?: Record<string, boolean>;
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

export type StrategyExperimentCandidate = {
  experiment_id: string;
  title: string;
  symbol: string;
  strategy_id: string;
  final_equity: number;
  return_pct: number;
  trade_count: number;
  marker_count: number;
  signal_count: number;
  tags: string[];
  review_checklist: Record<string, boolean>;
  created_at: string;
};

export type StrategyExperimentCandidateBoardResponse = {
  scope: "research_only";
  candidates: StrategyExperimentCandidate[];
};

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

export type PaperPosition = {
  position_id: string;
  account_id: string;
  symbol: string;
  asset_class: PaperIntent["asset_class"];
  quantity: number;
  average_price: number;
  updated_at: string;
};

export type PaperFill = {
  fill_id: string;
  intent_id: string;
  account_id: string;
  symbol: string;
  asset_class: PaperIntent["asset_class"];
  side: "buy" | "sell";
  quantity: number;
  fill_price: number;
  filled_at: string;
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

export type PaperAccountSummaryResponse = {
  scope: "paper_only";
  account: PaperAccount;
  positions: PaperPosition[];
  recent_intents: PaperIntent[];
  recent_fills: PaperFill[];
  recent_audit_events: PaperAuditEvent[];
};

export type PaperReferencePrice = {
  symbol: string;
  asset_class: PaperIntent["asset_class"];
  price: number;
  priced_at: string;
};

export type PaperPositionPnl = {
  position_id: string;
  account_id: string;
  symbol: string;
  asset_class: PaperIntent["asset_class"];
  quantity: number;
  average_price: number;
  multiplier: number;
  price_state: "fresh" | "stale" | "missing";
  reference_price: number | null;
  reference_priced_at: string | null;
  market_value: number | null;
  cost_basis: number | null;
  unrealized_pnl: number | null;
};

export type PaperPnlSnapshot = {
  account_id: string;
  base_currency: string;
  current_cash: number;
  as_of: string;
  price_state: "complete" | "partial";
  total_market_value: number;
  total_unrealized_pnl: number;
  total_realized_pnl: number;
  account_equity: number;
  positions: PaperPositionPnl[];
};

export type PaperPnlSnapshotResponse = {
  scope: "paper_only";
  snapshot: PaperPnlSnapshot;
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

export function listReportReviews(reportId: string): Promise<ReportReview[]> {
  return requestJson<ReportReview[]>(`/api/reports/${reportId}/reviews`);
}

export function createReportReview(reportId: string, payload: ReportReviewPayload): Promise<ReportReview> {
  return requestJson<ReportReview>(`/api/reports/${reportId}/reviews`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
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
  const end = formatLocalDate(new Date());
  const startDate = new Date();
  startDate.setDate(startDate.getDate() - 1);
  const start = formatLocalDate(startDate);
  return requestJson<DailyBarSyncResponse>("/api/market-data/sync-daily-bars", {
    method: "POST",
    body: JSON.stringify({
      symbol,
      start,
      end,
    }),
  });
}

function formatLocalDate(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function getOptionChain(underlying: string, expiry = nextFridayLocalDate()): Promise<OptionChainResponse> {
  return requestJson<OptionChainResponse>(
    `/api/options/chain?underlying=${encodeURIComponent(underlying)}&expiry=${encodeURIComponent(expiry)}`,
  );
}

function nextFridayLocalDate(): string {
  const value = new Date();
  value.setHours(0, 0, 0, 0);
  const daysUntilFriday = (5 - value.getDay() + 7) % 7 || 7;
  value.setDate(value.getDate() + daysUntilFriday);
  return formatLocalDate(value);
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
      strategy_id: payload.strategyId,
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

export function listStrategyCatalog(): Promise<StrategyCatalogResponse> {
  return requestJson<StrategyCatalogResponse>("/api/strategy-lab/strategies");
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
      tags: payload.tags ?? [],
      notes: payload.notes ?? null,
      report_id: payload.reportId ?? null,
    }),
  });
}

export function listStrategyExperiments(
  symbol?: string,
  options: { includeArchived?: boolean; tag?: string; reviewStatus?: StrategyExperimentReviewStatus | "all" } = {},
): Promise<StrategyExperimentListResponse> {
  const params = new URLSearchParams();
  if (symbol) {
    params.set("symbol", symbol);
  }
  if (options.includeArchived) {
    params.set("include_archived", "true");
  }
  if (options.tag) {
    params.set("tag", options.tag);
  }
  if (options.reviewStatus && options.reviewStatus !== "all") {
    params.set("review_status", options.reviewStatus);
  }
  const query = params.toString();
  return requestJson<StrategyExperimentListResponse>(`/api/strategy-lab/experiments${query ? `?${query}` : ""}`);
}

export function listStrategyExperimentCandidates(options: {
  symbol?: string;
  strategyId?: string;
  tag?: string;
  sortBy?: "created_at" | "return_pct";
  sortOrder?: "asc" | "desc";
} = {}): Promise<StrategyExperimentCandidateBoardResponse> {
  const params = new URLSearchParams();
  if (options.symbol) {
    params.set("symbol", options.symbol);
  }
  if (options.strategyId) {
    params.set("strategy_id", options.strategyId);
  }
  if (options.tag) {
    params.set("tag", options.tag);
  }
  if (options.sortBy) {
    params.set("sort_by", options.sortBy);
  }
  if (options.sortOrder) {
    params.set("sort_order", options.sortOrder);
  }
  const query = params.toString();
  return requestJson<StrategyExperimentCandidateBoardResponse>(
    `/api/strategy-lab/experiments/candidates${query ? `?${query}` : ""}`,
  );
}

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

export function getPaperAccountSummary(accountId: string): Promise<PaperAccountSummaryResponse> {
  return requestJson<PaperAccountSummaryResponse>(`/api/paper-trading/accounts/${accountId}/summary`);
}

export function createPaperPnlSnapshot(
  accountId: string,
  referencePrices: PaperReferencePrice[],
): Promise<PaperPnlSnapshotResponse> {
  return requestJson<PaperPnlSnapshotResponse>(`/api/paper-trading/accounts/${accountId}/pnl-snapshot`, {
    method: "POST",
    body: JSON.stringify({
      reference_prices: referencePrices.map((price) => ({
        symbol: price.symbol,
        asset_class: price.asset_class,
        price: price.price,
        priced_at: price.priced_at,
      })),
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

export function getStrategyExperiment(experimentId: string): Promise<StrategyExperiment> {
  return requestJson<StrategyExperiment>(`/api/strategy-lab/experiments/${experimentId}`);
}

export function duplicateStrategyExperiment(experimentId: string): Promise<StrategyExperiment> {
  return requestJson<StrategyExperiment>(`/api/strategy-lab/experiments/${experimentId}/duplicate`, {
    method: "POST",
  });
}

export function updateStrategyExperiment(
  experimentId: string,
  payload: StrategyExperimentUpdatePayload,
): Promise<StrategyExperiment> {
  return requestJson<StrategyExperiment>(`/api/strategy-lab/experiments/${experimentId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
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
