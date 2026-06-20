import { useEffect, useId, useMemo, useRef, useState } from "react";
import {
  CandlestickSeries,
  ColorType,
  createChart,
  createSeriesMarkers,
  HistogramSeries,
  LineSeries,
  type CandlestickData,
  type HistogramData,
  type LineData,
  type SeriesMarker,
  type Time,
} from "lightweight-charts";
import {
  Activity,
  Archive,
  ArchiveRestore,
  BadgeCheck,
  ChartNoAxesCombined,
  CheckCircle2,
  ClipboardCheck,
  Copy,
  FileText,
  FlaskConical,
  GitCompareArrows,
  History,
  Layers3,
  ListChecks,
  RefreshCw,
  Save,
  ShieldCheck,
  SlidersHorizontal,
  Tag,
  WalletCards,
  XCircle,
} from "lucide-react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Toggle } from "@/components/ui/toggle";
import {
  compareStrategyExperiments,
  cancelPaperIntent,
  createPaperAccount,
  createPaperIntentDraft,
  createPaperPnlSnapshot,
  duplicateStrategyExperiment,
  getPaperAccountSummary,
  getStrategyExperiment,
  listPaperAccounts,
  listStrategyCatalog,
  listStrategyExperimentCandidates,
  listStrategyExperiments,
  previewSignalStrategy,
  reviewPaperIntent,
  runPaperIntentRiskCheck,
  saveStrategyExperiment,
  submitPaperIntent,
  updateStrategyExperiment,
  type MarketBar,
  type PaperAccount,
  type PaperAccountSummaryResponse,
  type PaperIntentResponse,
  type PaperPnlSnapshotResponse,
  type PaperReferencePrice,
  type ReportListItem,
  type StrategyCatalogItem,
  type StrategyExperimentCandidate,
  type StrategyExperimentComparison,
  type StrategyExperiment,
  type StrategyExperimentReviewStatus,
  type StrategyPreviewResponse,
} from "@/lib/api";

type StrategyLabPanelProps = {
  symbol: string;
  bars: MarketBar[];
  latestReport: ReportListItem | null;
  onRefreshMarket: () => void;
};

type PaperRetryAction = "loadAccounts" | "createDraft" | "riskCheck" | "approve" | "reject" | "submit" | "cancel";
type WorkflowStepTone = "complete" | "current" | "empty" | "updating";

export function StrategyLabPanel({
  symbol,
  bars,
  latestReport,
  onRefreshMarket,
}: StrategyLabPanelProps) {
  const [strategies, setStrategies] = useState<StrategyCatalogItem[]>([]);
  const [selectedStrategyId, setSelectedStrategyId] = useState("ma-cross-research");
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [fastWindow, setFastWindow] = useState(2);
  const [slowWindow, setSlowWindow] = useState(3);
  const [initialEquity, setInitialEquity] = useState(10_000);
  const [preview, setPreview] = useState<StrategyPreviewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [experiments, setExperiments] = useState<StrategyExperiment[]>([]);
  const [experimentsLoading, setExperimentsLoading] = useState(false);
  const [experimentsError, setExperimentsError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [activeExperimentId, setActiveExperimentId] = useState<string | null>(null);
  const [experimentTags, setExperimentTags] = useState("draft");
  const [experimentNotes, setExperimentNotes] = useState("");
  const [tagFilter, setTagFilter] = useState("");
  const [reviewFilter, setReviewFilter] = useState<StrategyExperimentReviewStatus | "all">("all");
  const [showArchived, setShowArchived] = useState(false);
  const [compareBaseId, setCompareBaseId] = useState<string | null>(null);
  const [compareCandidateId, setCompareCandidateId] = useState<string | null>(null);
  const [comparison, setComparison] = useState<StrategyExperimentComparison | null>(null);
  const [comparisonLoading, setComparisonLoading] = useState(false);
  const [comparisonError, setComparisonError] = useState<string | null>(null);
  const [candidates, setCandidates] = useState<StrategyExperimentCandidate[]>([]);
  const [candidatesLoading, setCandidatesLoading] = useState(false);
  const [candidatesError, setCandidatesError] = useState<string | null>(null);
  const [candidateTagFilter, setCandidateTagFilter] = useState("");
  const [candidateSortBy, setCandidateSortBy] = useState<"created_at" | "return_pct">("return_pct");
  const [paperAccounts, setPaperAccounts] = useState<PaperAccount[]>([]);
  const [paperIntent, setPaperIntent] = useState<PaperIntentResponse | null>(null);
  const [paperLoading, setPaperLoading] = useState(false);
  const [paperError, setPaperError] = useState<string | null>(null);
  const [paperRetryAction, setPaperRetryAction] = useState<PaperRetryAction>("loadAccounts");
  const [paperSummary, setPaperSummary] = useState<PaperAccountSummaryResponse | null>(null);
  const [paperPnl, setPaperPnl] = useState<PaperPnlSnapshotResponse | null>(null);
  const [paperDashboardLoading, setPaperDashboardLoading] = useState(false);
  const [paperDashboardError, setPaperDashboardError] = useState<string | null>(null);
  const previewBars = useMemo(() => bars.slice(-80), [bars]);
  const canPreview = previewBars.length >= Math.max(fastWindow, slowWindow);
  const selectedStrategy = strategies.find((strategy) => strategy.strategy_id === selectedStrategyId) ?? null;

  useEffect(() => {
    void loadCatalog();
  }, []);

  useEffect(() => {
    void loadPaperAccounts();
  }, []);

  useEffect(() => {
    void loadExperiments();
  }, [symbol, showArchived, tagFilter, reviewFilter]);

  useEffect(() => {
    void loadCandidates();
  }, [symbol, candidateTagFilter, candidateSortBy]);

  useEffect(() => {
    setCompareBaseId(null);
    setCompareCandidateId(null);
    setComparison(null);
    setComparisonError(null);
  }, [symbol]);

  useEffect(() => {
    if (!compareBaseId || !compareCandidateId || compareBaseId === compareCandidateId) {
      setComparison(null);
      return;
    }
    const timeout = window.setTimeout(() => {
      void loadComparison(compareBaseId, compareCandidateId);
    }, 120);
    return () => window.clearTimeout(timeout);
  }, [compareBaseId, compareCandidateId]);

  useEffect(() => {
    if (!canPreview) {
      setPreview(null);
      return;
    }
    const timeout = window.setTimeout(() => {
      void loadPreview();
    }, 180);
    return () => window.clearTimeout(timeout);
  }, [symbol, selectedStrategyId, fastWindow, slowWindow, initialEquity, previewBars, canPreview]);

  async function loadPreview() {
    setLoading(true);
    setError(null);
    try {
      const response = await previewSignalStrategy({
        symbol,
        strategyId: selectedStrategyId,
        fastWindow,
        slowWindow,
        initialEquity,
        bars: previewBars,
        reportId: latestReport?.report_id ?? null,
      });
      setPreview(response);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "SignalStrategy preview failed.");
    } finally {
      setLoading(false);
    }
  }

  async function loadCatalog() {
    setCatalogError(null);
    try {
      const response = await listStrategyCatalog();
      setStrategies(response.strategies);
      const defaultStrategy = response.strategies[0];
      if (defaultStrategy) {
        setSelectedStrategyId(defaultStrategy.strategy_id);
        setFastWindow(Number(defaultStrategy.default_parameters.fast_window ?? 2));
        setSlowWindow(Number(defaultStrategy.default_parameters.slow_window ?? 3));
      }
    } catch (caught) {
      setCatalogError(caught instanceof Error ? caught.message : "Strategy catalog failed to load.");
    }
  }

  async function loadExperiments(nextActiveExperimentId = activeExperimentId) {
    setExperimentsLoading(true);
    setExperimentsError(null);
    try {
      const response = await listStrategyExperiments(symbol, {
        includeArchived: showArchived,
        tag: tagFilter.trim() || undefined,
        reviewStatus: reviewFilter,
      });
      setExperiments(response.experiments);
      if (nextActiveExperimentId) {
        setActiveExperimentId(nextActiveExperimentId);
      }
    } catch (caught) {
      setExperimentsError(caught instanceof Error ? caught.message : "Strategy experiments failed to load.");
    } finally {
      setExperimentsLoading(false);
    }
  }

  async function loadCandidates() {
    setCandidatesLoading(true);
    setCandidatesError(null);
    try {
      const response = await listStrategyExperimentCandidates({
        symbol,
        tag: candidateTagFilter.trim() || undefined,
        sortBy: candidateSortBy,
        sortOrder: "desc",
      });
      setCandidates(response.candidates);
    } catch (caught) {
      setCandidatesError(caught instanceof Error ? caught.message : "Strategy candidates failed to load.");
    } finally {
      setCandidatesLoading(false);
    }
  }

  async function saveCurrentExperiment() {
    if (!preview) return;
    setSaving(true);
    setError(null);
    try {
      const saved = await saveStrategyExperiment({
        title: `${symbol.toUpperCase()} ${fastWindow}/${slowWindow} ${selectedStrategy?.name ?? "Strategy"}`,
        symbol,
        strategyId: preview.strategy.strategy_id,
        parameters: preview.strategy.parameters,
        preview,
        tags: parseTags(experimentTags),
        notes: experimentNotes.trim() || null,
        reportId: latestReport?.report_id ?? null,
      });
      setActiveExperimentId(saved.experiment_id);
      await loadExperiments(saved.experiment_id);
      await loadCandidates();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Strategy experiment save failed.");
    } finally {
      setSaving(false);
    }
  }

  async function openExperiment(experimentId: string) {
    setExperimentsError(null);
    try {
      const experiment = await getStrategyExperiment(experimentId);
      setFastWindow(Number(experiment.parameters.fast_window ?? 2));
      setSlowWindow(Number(experiment.parameters.slow_window ?? 3));
      setExperimentTags(experiment.tags.join(", "));
      setExperimentNotes(experiment.notes ?? "");
      setPreview(experiment.preview);
      setActiveExperimentId(experiment.experiment_id);
    } catch (caught) {
      setExperimentsError(caught instanceof Error ? caught.message : "Strategy experiment failed to open.");
    }
  }

  async function duplicateExperiment(experimentId: string) {
    setExperimentsError(null);
    try {
      const duplicated = await duplicateStrategyExperiment(experimentId);
      setActiveExperimentId(duplicated.experiment_id);
      await loadExperiments(duplicated.experiment_id);
      await loadCandidates();
    } catch (caught) {
      setExperimentsError(caught instanceof Error ? caught.message : "Strategy experiment duplicate failed.");
    }
  }

  async function setExperimentArchived(experiment: StrategyExperiment, archived: boolean) {
    setExperimentsError(null);
    try {
      const updated = await updateStrategyExperiment(experiment.experiment_id, { archived });
      if (archived && activeExperimentId === updated.experiment_id) {
        setActiveExperimentId(null);
      }
      await loadExperiments(archived ? null : updated.experiment_id);
      await loadCandidates();
    } catch (caught) {
      setExperimentsError(caught instanceof Error ? caught.message : "Strategy experiment archive update failed.");
    }
  }

  async function setExperimentReviewStatus(experiment: StrategyExperiment, reviewStatus: StrategyExperimentReviewStatus) {
    setExperimentsError(null);
    try {
      const updated = await updateStrategyExperiment(experiment.experiment_id, {
        review_status: reviewStatus,
        review_checklist: buildReviewChecklist(reviewStatus),
      });
      await loadExperiments(updated.experiment_id);
      await loadCandidates();
    } catch (caught) {
      setExperimentsError(caught instanceof Error ? caught.message : "Strategy experiment review update failed.");
    }
  }

  async function archiveCandidate(experimentId: string) {
    setCandidatesError(null);
    try {
      await updateStrategyExperiment(experimentId, { archived: true });
      await loadExperiments(activeExperimentId);
      await loadCandidates();
    } catch (caught) {
      setCandidatesError(caught instanceof Error ? caught.message : "Strategy candidate archive failed.");
    }
  }

  async function setCandidateReviewStatus(experimentId: string, reviewStatus: StrategyExperimentReviewStatus) {
    setCandidatesError(null);
    try {
      await updateStrategyExperiment(experimentId, {
        review_status: reviewStatus,
        review_checklist: buildReviewChecklist(reviewStatus),
      });
      await loadExperiments(activeExperimentId);
      await loadCandidates();
    } catch (caught) {
      setCandidatesError(caught instanceof Error ? caught.message : "Strategy candidate review update failed.");
    }
  }

  async function loadPaperAccounts() {
    setPaperRetryAction("loadAccounts");
    setPaperError(null);
    try {
      const response = await listPaperAccounts();
      setPaperAccounts(response.accounts);
      const activeAccount = response.accounts.find((account) => account.status === "active") ?? null;
      if (activeAccount) {
        await loadPaperDashboard(activeAccount);
      }
    } catch (caught) {
      setPaperError(caught instanceof Error ? caught.message : "Paper accounts failed to load.");
    }
  }

  async function ensurePaperAccount(): Promise<PaperAccount> {
    const existing = paperAccounts.find((account) => account.status === "active");
    if (existing) return existing;
    const created = await createPaperAccount();
    setPaperAccounts([created.account]);
    await loadPaperDashboard(created.account);
    return created.account;
  }

  async function loadPaperDashboard(account: PaperAccount | null = paperAccounts.find((item) => item.status === "active") ?? null) {
    if (!account) {
      setPaperSummary(null);
      setPaperPnl(null);
      return;
    }
    setPaperDashboardLoading(true);
    setPaperDashboardError(null);
    try {
      const summary = await getPaperAccountSummary(account.account_id);
      setPaperSummary(summary);
      const pnl = await createPaperPnlSnapshot(account.account_id, buildPaperReferencePrices(summary, bars));
      setPaperPnl(pnl);
    } catch (caught) {
      setPaperDashboardError(caught instanceof Error ? caught.message : "Paper risk dashboard failed to load.");
    } finally {
      setPaperDashboardLoading(false);
    }
  }

  async function createPaperDraftFromCandidate(candidate: StrategyExperimentCandidate) {
    setPaperLoading(true);
    setPaperRetryAction("createDraft");
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
    setPaperRetryAction("riskCheck");
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
    setPaperRetryAction(decision);
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
    setPaperRetryAction("submit");
    setPaperError(null);
    try {
      setPaperIntent(await submitPaperIntent(paperIntent.intent.intent_id));
      const activeAccount = paperAccounts.find((account) => account.account_id === paperIntent.intent.account_id) ?? null;
      await loadPaperDashboard(activeAccount);
    } catch (caught) {
      setPaperError(caught instanceof Error ? caught.message : "Paper simulation submit failed.");
    } finally {
      setPaperLoading(false);
    }
  }

  async function cancelSelectedPaperIntent() {
    if (!paperIntent) return;
    setPaperLoading(true);
    setPaperRetryAction("cancel");
    setPaperError(null);
    try {
      setPaperIntent(await cancelPaperIntent(paperIntent.intent.intent_id));
    } catch (caught) {
      setPaperError(caught instanceof Error ? caught.message : "Paper cancellation failed.");
    } finally {
      setPaperLoading(false);
    }
  }

  async function loadComparison(baseId: string, candidateId: string) {
    setComparisonLoading(true);
    setComparisonError(null);
    try {
      const response = await compareStrategyExperiments(baseId, candidateId);
      setComparison(response);
    } catch (caught) {
      setComparison(null);
      setComparisonError(caught instanceof Error ? caught.message : "Strategy experiment comparison failed.");
    } finally {
      setComparisonLoading(false);
    }
  }

  function markLiveEdit() {
    setActiveExperimentId(null);
  }

  function retryPaperAction() {
    if (!paperIntent || paperRetryAction === "loadAccounts" || paperRetryAction === "createDraft") {
      void loadPaperAccounts();
      return;
    }
    if (paperRetryAction === "riskCheck") {
      void runSelectedPaperRiskCheck();
      return;
    }
    if (paperRetryAction === "approve" || paperRetryAction === "reject") {
      void reviewSelectedPaperIntent(paperRetryAction);
      return;
    }
    if (paperRetryAction === "submit") {
      void submitSelectedPaperIntent();
      return;
    }
    void cancelSelectedPaperIntent();
  }

  const latestSignal = preview?.signals[preview.signals.length - 1];
  const tradeCount = preview?.backtest.trades.length ?? 0;
  const markerCount = preview?.overlay.markers.length ?? 0;
  const activeExperiment = experiments.find((experiment) => experiment.experiment_id === activeExperimentId);
  const buyCount = preview?.signals.filter((row) => row.signal === 1).length ?? 0;
  const exitCount = preview?.signals.filter((row) => row.signal === -1).length ?? 0;
  const paperActionState = paperIntent ? getPaperActionState(paperIntent) : null;
  const paperActionDetailsId = useId();
  const paperDisabledReasons = paperIntent && paperActionState ? getPaperDisabledReasons(paperIntent, paperActionState) : [];
  const activePaperAccount = paperAccounts.find((account) => account.status === "active") ?? null;
  const candidateStepValue = candidatesLoading ? "Updating" : candidates.length > 0 ? `${candidates.length} ready` : "No candidates";
  const candidateStepTone: WorkflowStepTone = candidatesLoading ? "updating" : candidates.length > 0 ? "complete" : "empty";
  const paperStepValue = paperIntent ? paperIntentStatusLabel(paperIntent.intent.status) : "No draft";
  const paperStepTone: WorkflowStepTone = paperLoading
    ? "updating"
    : paperIntent?.intent.status === "paper_filled"
      ? "complete"
      : paperIntent
        ? "current"
        : "empty";
  const workflowSteps = [
    { label: "Catalog", value: selectedStrategy?.name ?? "Loading", tone: selectedStrategy ? "complete" : "updating" },
    { label: "Preview", value: loading ? "Updating" : preview ? "Live" : canPreview ? "Ready" : "Waiting", tone: loading ? "updating" : preview ? "complete" : canPreview ? "current" : "empty" },
    { label: "Candidate", value: candidateStepValue, tone: candidateStepTone },
    { label: "Paper", value: paperStepValue, tone: paperStepTone },
  ];

  return (
    <div className="grid gap-4">
      <section className="rounded-lg border bg-card">
        <div className="flex flex-col gap-4 border-b p-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex size-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
                <FlaskConical className="size-4" />
              </div>
              <div>
                <h2 className="text-xl font-semibold tracking-normal">{symbol.toUpperCase()} Strategy Lab</h2>
                <p className="text-sm text-muted-foreground">
                  Research-only signal design, preview, saved experiments, and report-linked notes.
                </p>
              </div>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline">research_only</Badge>
            <Button type="button" variant="outline" onClick={onRefreshMarket} className="gap-2">
              <RefreshCw className="size-4" />
              Refresh Bars
            </Button>
            <Button type="button" onClick={saveCurrentExperiment} disabled={!preview || saving} className="gap-2">
              <Save className="size-4" />
              {saving ? "Saving" : "Save Experiment"}
            </Button>
          </div>
        </div>
        <div className="grid gap-3 p-4 sm:grid-cols-2 xl:grid-cols-4">
          {workflowSteps.map((step) => (
            <WorkflowStep key={step.label} label={step.label} value={step.value} tone={step.tone as WorkflowStepTone} />
          ))}
        </div>
      </section>

      <div className="grid gap-4 2xl:grid-cols-[340px_minmax(0,1fr)_360px]">
        <aside className="grid gap-4 content-start">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <SlidersHorizontal className="size-4" />
                Research Controls
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4">
              <div className="rounded-md border bg-muted/20 p-3 text-sm">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs text-muted-foreground">Strategy</span>
                  <Badge variant="secondary">{selectedStrategy?.scope ?? "research_only"}</Badge>
                </div>
                <div className="mt-1 font-medium">{selectedStrategy?.strategy_id ?? selectedStrategyId}</div>
                <div className="mt-1 text-xs leading-5 text-muted-foreground">
                  {selectedStrategy?.description ?? "Loading strategy catalog."}
                </div>
              </div>
              {catalogError ? (
                <RetryAlert
                  message={catalogError}
                  actionLabel="Reload catalog"
                  onRetry={() => void loadCatalog()}
                />
              ) : null}
              <div className="grid gap-3">
                <label className="grid gap-1">
                  <span className="text-xs text-muted-foreground">Fast Window</span>
                  <Input
                    type="number"
                    min={1}
                    max={100}
                    value={fastWindow}
                    onChange={(event) => {
                      const nextFastWindow = Number(event.target.value);
                      markLiveEdit();
                      setFastWindow(nextFastWindow);
                      setSlowWindow((current) => Math.max(current, nextFastWindow));
                    }}
                  />
                </label>
                <label className="grid gap-1">
                  <span className="text-xs text-muted-foreground">Slow Window</span>
                  <Input
                    type="number"
                    min={1}
                    max={200}
                    value={slowWindow}
                    onChange={(event) => {
                      markLiveEdit();
                      setSlowWindow(Math.max(Number(event.target.value), fastWindow));
                    }}
                  />
                </label>
                <label className="grid gap-1">
                  <span className="text-xs text-muted-foreground">Initial Equity</span>
                  <Input
                    type="number"
                    min={1}
                    step={100}
                    value={initialEquity}
                    onChange={(event) => {
                      markLiveEdit();
                      setInitialEquity(Number(event.target.value));
                    }}
                  />
                </label>
                <label className="grid gap-1">
                  <span className="text-xs text-muted-foreground">Tags</span>
                  <Input
                    value={experimentTags}
                    onChange={(event) => setExperimentTags(event.target.value)}
                    placeholder="draft, breakout"
                  />
                </label>
                <label className="grid gap-1">
                  <span className="text-xs text-muted-foreground">Notes</span>
                  <Input
                    value={experimentNotes}
                    onChange={(event) => setExperimentNotes(event.target.value)}
                    placeholder="Research note"
                  />
                </label>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <MetricTile label="Bars" value={previewBars.length.toString()} />
                <MetricTile label="Latest" value={signalLabel(latestSignal?.signal ?? 0)} tone={signalTone(latestSignal?.signal ?? 0)} />
              </div>
              {activeExperiment ? (
                <div className="rounded-md border bg-muted/20 p-3 text-xs text-muted-foreground">
                  Opened: <span className="font-medium text-foreground">{activeExperiment.title}</span>
                </div>
              ) : null}
              {!canPreview ? (
                <Alert>
                  <AlertDescription>
                    Need at least {Math.max(fastWindow, slowWindow)} bars for the current window.
                  </AlertDescription>
                </Alert>
              ) : null}
              {error ? (
                <RetryAlert
                  message={error}
                  actionLabel="Refresh preview"
                  onRetry={() => {
                    if (canPreview) void loadPreview();
                  }}
                />
              ) : null}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Activity className="size-4" />
                Research Backtest
              </CardTitle>
            </CardHeader>
            <CardContent className="grid gap-2">
              <MetricTile label="Initial" value={formatCurrency(preview?.backtest.initial_equity)} />
              <MetricTile label="Final" value={formatCurrency(preview?.backtest.final_equity)} tone={(preview?.backtest.return_pct ?? 0) >= 0 ? "positive" : "negative"} />
              <MetricTile label="Return" value={`${preview?.backtest.return_pct ?? 0}%`} tone={(preview?.backtest.return_pct ?? 0) >= 0 ? "positive" : "negative"} />
              <MetricTile label="Trades" value={tradeCount.toString()} />
            </CardContent>
          </Card>
        </aside>

        <main className="grid gap-4 content-start">
          <Card>
            <CardHeader className="pb-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <ChartNoAxesCombined className="size-5" />
                  {symbol.toUpperCase()} Signal Overlay
                </CardTitle>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant={loading ? "secondary" : "default"}>{loading ? "Updating" : "Live Preview"}</Badge>
                  <Badge variant="outline">{fastWindow}/{slowWindow} windows</Badge>
                </div>
              </div>
            </CardHeader>
            <CardContent className="grid gap-4">
              <StrategyOverlayChart
                preview={preview}
                bars={previewBars}
                fastWindow={fastWindow}
                slowWindow={slowWindow}
              />
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                <MetricTile label="Markers" value={markerCount.toString()} />
                <MetricTile label="Buy Signals" value={buyCount.toString()} tone="positive" />
                <MetricTile label="Exit Signals" value={exitCount.toString()} tone="negative" />
                <MetricTile label="Scope" value={preview?.scope ?? "research_only"} />
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <ListChecks className="size-4" />
                  Signal Rows
                </CardTitle>
              </CardHeader>
              <CardContent>
                <SignalRowsTable preview={preview} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <FileText className="size-4" />
                  Report Note
                </CardTitle>
              </CardHeader>
              <CardContent>
                {preview?.note ? (
                  <div className="grid gap-2 text-sm">
                    <div className="font-medium">{String(preview.note.title)}</div>
                    <div className="text-muted-foreground">{String(preview.note.body)}</div>
                    <div className="flex flex-wrap gap-2">
                      {Array.isArray(preview.note.evidence_labels)
                        ? preview.note.evidence_labels.map((label) => (
                            <Badge key={String(label)} variant="outline">
                              {String(label)}
                            </Badge>
                          ))
                        : null}
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No linked report selected for this symbol.</p>
                )}
              </CardContent>
            </Card>
          </div>
        </main>

        <aside className="grid gap-4 content-start">
          <Card>
            <CardHeader className="pb-3">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <History className="size-4" />
                  Experiment Rail
                </CardTitle>
                <Button type="button" variant="outline" size="sm" onClick={() => void loadExperiments()} className="gap-2">
                  <RefreshCw className="size-4" />
                  Refresh
                </Button>
                <Toggle
                  pressed={showArchived}
                  onPressedChange={setShowArchived}
                  variant="outline"
                  size="sm"
                  aria-label="Show archived experiments"
                  className="gap-2"
                >
                  <Archive className="size-4" />
                  Archived
                </Toggle>
              </div>
            </CardHeader>
            <CardContent className="grid gap-3">
              <label className="grid gap-1">
                <span className="text-xs text-muted-foreground">Filter tag</span>
                <Input
                  value={tagFilter}
                  onChange={(event) => setTagFilter(event.target.value)}
                  placeholder="draft"
                />
              </label>
              <label className="grid gap-1">
                <span className="text-xs text-muted-foreground">Review status</span>
                <select
                  value={reviewFilter}
                  onChange={(event) => setReviewFilter(event.target.value as StrategyExperimentReviewStatus | "all")}
                  className="h-10 rounded-md border border-input bg-background px-3 text-sm"
                >
                  <option value="all">All</option>
                  <option value="draft">Draft</option>
                  <option value="reviewed">Reviewed</option>
                  <option value="candidate">Candidate</option>
                  <option value="rejected">Rejected</option>
                </select>
              </label>
              {experimentsError ? (
                <RetryAlert
                  message={experimentsError}
                  actionLabel="Reload experiments"
                  onRetry={() => void loadExperiments()}
                />
              ) : null}
              {experimentsLoading ? (
                <LoadingRows label="Loading experiments" />
              ) : experiments.length === 0 ? (
                <p className="text-sm text-muted-foreground">No saved experiments for {symbol.toUpperCase()} yet.</p>
              ) : (
                <div className="grid max-h-[560px] gap-2 overflow-y-auto pr-1">
                  {experiments.map((experiment) => (
                    <ExperimentRailItem
                      key={experiment.experiment_id}
                      experiment={experiment}
                      selected={experiment.experiment_id === activeExperimentId}
                      compareBaseSelected={compareBaseId === experiment.experiment_id}
                      compareCandidateSelected={compareCandidateId === experiment.experiment_id}
                      onOpen={() => void openExperiment(experiment.experiment_id)}
                      onDuplicate={() => void duplicateExperiment(experiment.experiment_id)}
                      onUseAsBase={() => setCompareBaseId(experiment.experiment_id)}
                      onUseAsCandidate={() => setCompareCandidateId(experiment.experiment_id)}
                      onArchive={() => void setExperimentArchived(experiment, !experiment.archived)}
                      onReview={(status) => void setExperimentReviewStatus(experiment, status)}
                    />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <ExperimentComparisonPanel
            comparison={comparison}
            comparisonLoading={comparisonLoading}
            comparisonError={comparisonError}
            baseTitle={experiments.find((experiment) => experiment.experiment_id === compareBaseId)?.title ?? null}
            candidateTitle={experiments.find((experiment) => experiment.experiment_id === compareCandidateId)?.title ?? null}
            onRetry={() => {
              if (compareBaseId && compareCandidateId) void loadComparison(compareBaseId, compareCandidateId);
            }}
          />
        </aside>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <BadgeCheck className="size-4" />
              Candidate Review Board
            </CardTitle>
            <Button type="button" variant="outline" size="sm" onClick={() => void loadCandidates()} className="gap-2">
              <RefreshCw className="size-4" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent className="grid gap-3">
          <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_180px]">
            <label className="grid gap-1">
              <span className="text-xs text-muted-foreground">Candidate tag</span>
              <Input
                value={candidateTagFilter}
                onChange={(event) => setCandidateTagFilter(event.target.value)}
                placeholder="breakout"
              />
            </label>
            <label className="grid gap-1">
              <span className="text-xs text-muted-foreground">Sort</span>
              <select
                value={candidateSortBy}
                onChange={(event) => setCandidateSortBy(event.target.value as "created_at" | "return_pct")}
                className="h-10 rounded-md border border-input bg-background px-3 text-sm"
              >
                <option value="return_pct">Return</option>
                <option value="created_at">Created</option>
              </select>
            </label>
          </div>
          {candidatesError ? (
            <RetryAlert
              message={candidatesError}
              actionLabel="Reload candidates"
              onRetry={() => void loadCandidates()}
            />
          ) : null}
          {candidatesLoading ? (
            <LoadingRows label="Loading candidates" />
          ) : candidates.length === 0 ? (
            <p className="text-sm text-muted-foreground">No candidate experiments for {symbol.toUpperCase()}.</p>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Candidate</TableHead>
                    <TableHead>Return</TableHead>
                    <TableHead>Trades</TableHead>
                    <TableHead>Checklist</TableHead>
                    <TableHead>Tags</TableHead>
                    <TableHead className="w-[300px]">Candidate actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {candidates.map((candidate) => (
                    <CandidateBoardRow
                      key={candidate.experiment_id}
                      candidate={candidate}
                      onOpen={() => void openExperiment(candidate.experiment_id)}
                      onUseAsBase={() => setCompareBaseId(candidate.experiment_id)}
                      onUseAsCandidate={() => setCompareCandidateId(candidate.experiment_id)}
                      onReject={() => void setCandidateReviewStatus(candidate.experiment_id, "rejected")}
                      onArchive={() => void archiveCandidate(candidate.experiment_id)}
                      onCreatePaperDraft={() => void createPaperDraftFromCandidate(candidate)}
                      paperLoading={paperLoading}
                    />
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <ShieldCheck className="size-4" />
            Paper Review
          </CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3">
          {paperError ? (
            <RetryAlert
              message={paperError}
              actionLabel={paperRetryActionLabel(paperIntent, paperRetryAction)}
              onRetry={retryPaperAction}
            />
          ) : null}
          {!paperIntent ? (
            <p className="text-sm text-muted-foreground">Select Paper Draft from a candidate experiment to start a paper-only review.</p>
          ) : (
            <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_320px]">
              <div className="rounded-md border p-3">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant="outline">{paperIntent.scope}</Badge>
                      <Badge variant={paperIntent.intent.status === "risk_rejected" ? "destructive" : "secondary"}>
                        {paperIntentStatusLabel(paperIntent.intent.status)}
                      </Badge>
                      <span className="text-sm font-medium">{paperIntent.intent.symbol}</span>
                    </div>
                    <p className="mt-2 max-w-2xl text-xs leading-5 text-muted-foreground">
                      Local paper simulation only. This review does not connect to a broker, live account, or automatic execution path.
                    </p>
                  </div>
                  <Badge variant="outline" className="shrink-0">
                    Human gated
                  </Badge>
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
                {paperActionState ? (
                  <div id={paperActionDetailsId} className="mt-3 rounded-md border bg-muted/20 p-3 text-sm" aria-live="polite">
                    <div className="flex items-center gap-2 font-medium">
                      <ShieldCheck className="size-4" />
                      Next paper step
                    </div>
                    <p className="mt-1 text-muted-foreground">{paperActionState.nextStep}</p>
                    <p className="mt-2 text-xs text-muted-foreground">{paperActionState.blocker}</p>
                    {paperDisabledReasons.length > 0 ? (
                      <div className="mt-3 border-t pt-2 text-xs text-muted-foreground">
                        <div className="font-medium text-foreground">Locked controls</div>
                        <ul className="mt-1 list-disc space-y-1 pl-4">
                          {paperDisabledReasons.map((item) => (
                            <li key={item.label}>
                              <span className="font-medium text-foreground">{item.label}:</span> {item.reason}
                            </li>
                          ))}
                        </ul>
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </div>
              <div className="grid content-start gap-3 rounded-md border bg-muted/20 p-3">
                <div>
                  <div className="text-xs font-medium text-muted-foreground">Review gate</div>
                  <div className="mt-2 grid gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      className="min-h-11 whitespace-normal sm:min-h-0 sm:whitespace-nowrap"
                      onClick={() => void runSelectedPaperRiskCheck()}
                      disabled={paperLoading || !paperActionState?.canRiskCheck}
                      aria-describedby={paperActionDetailsId}
                    >
                      {paperLoading ? "Updating" : "Run RiskGuard"}
                    </Button>
                    <div className="grid gap-2 sm:grid-cols-2">
                      <Button
                        type="button"
                        variant="outline"
                        className="min-h-11 whitespace-normal sm:min-h-0 sm:whitespace-nowrap"
                        onClick={() => void reviewSelectedPaperIntent("approve")}
                        disabled={paperLoading || !paperActionState?.canApprove}
                        aria-describedby={paperActionDetailsId}
                      >
                        Approve Paper
                      </Button>
                      <Button
                        type="button"
                        variant="outline"
                        className="min-h-11 whitespace-normal sm:min-h-0 sm:whitespace-nowrap"
                        onClick={() => void reviewSelectedPaperIntent("reject")}
                        disabled={paperLoading || !paperActionState?.canReject}
                        aria-describedby={paperActionDetailsId}
                      >
                        Reject Paper
                      </Button>
                    </div>
                  </div>
                </div>
                <div className="border-t pt-3">
                  <div className="text-xs font-medium text-muted-foreground">Paper simulation</div>
                  <div className="mt-2 grid gap-2">
                    <Button
                      type="button"
                      className="min-h-11 whitespace-normal sm:min-h-0 sm:whitespace-nowrap"
                      onClick={() => void submitSelectedPaperIntent()}
                      disabled={paperLoading || !paperActionState?.canSubmit}
                      aria-describedby={paperActionDetailsId}
                    >
                      Paper Submit
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      className="min-h-11 whitespace-normal sm:min-h-0 sm:whitespace-nowrap"
                      onClick={() => void cancelSelectedPaperIntent()}
                      disabled={paperLoading || !paperActionState?.canCancel}
                      aria-describedby={paperActionDetailsId}
                    >
                      Cancel Paper
                    </Button>
                  </div>
                </div>
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

      <Card>
        <CardHeader className="pb-3">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <CardTitle className="flex items-center gap-2 text-base">
              <WalletCards className="size-4" />
              Paper Risk Dashboard
            </CardTitle>
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="gap-2"
              disabled={paperDashboardLoading || !activePaperAccount}
              onClick={() => void loadPaperDashboard(activePaperAccount)}
            >
              <RefreshCw className="size-4" />
              {paperDashboardLoading ? "Refreshing" : "Refresh"}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="grid gap-3">
          {paperDashboardError ? (
            <RetryAlert
              message={paperDashboardError}
              actionLabel="Reload dashboard"
              onRetry={() => void loadPaperDashboard(activePaperAccount)}
            />
          ) : null}
          {!activePaperAccount ? (
            <p className="text-sm text-muted-foreground">Create or load an active paper account to inspect paper risk state.</p>
          ) : paperDashboardLoading && !paperSummary ? (
            <LoadingRows label="Loading paper risk dashboard" />
          ) : (
            <PaperRiskDashboard summary={paperSummary} pnl={paperPnl} />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <Layers3 className="size-4" />
            Saved Experiment Table
          </CardTitle>
        </CardHeader>
        <CardContent>
          {experimentsLoading ? (
            <LoadingRows label="Loading experiments" />
          ) : experiments.length === 0 ? (
            <p className="text-sm text-muted-foreground">No saved experiments for {symbol.toUpperCase()} yet.</p>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead>
                    <TableHead>Metadata</TableHead>
                    <TableHead>Windows</TableHead>
                    <TableHead>Final Equity</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="w-[260px]">Compare / archive</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {experiments.map((experiment) => (
                    <TableRow key={experiment.experiment_id} data-state={experiment.experiment_id === activeExperimentId ? "selected" : undefined}>
                      <TableCell className="min-w-[220px]">
                        <div className="font-medium">{experiment.title}</div>
                        <div className="text-xs text-muted-foreground">{experiment.strategy_id}</div>
                      </TableCell>
                      <TableCell className="min-w-[220px]">
                        <ExperimentMetadata experiment={experiment} />
                      </TableCell>
                      <TableCell className="whitespace-nowrap">
                        {String(experiment.parameters.fast_window ?? "-")} / {String(experiment.parameters.slow_window ?? "-")}
                      </TableCell>
                      <TableCell className="whitespace-nowrap">{formatCurrency(experiment.preview.backtest.final_equity)}</TableCell>
                      <TableCell className="whitespace-nowrap">{formatTime(experiment.created_at)}</TableCell>
                      <TableCell>
                        <div className="grid gap-2">
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="w-14 text-xs text-muted-foreground">Compare</span>
                            <Button
                              type="button"
                              size="icon"
                              variant={compareBaseId === experiment.experiment_id ? "default" : "outline"}
                              aria-label={`Use ${experiment.title} as comparison A`}
                              onClick={() => setCompareBaseId(experiment.experiment_id)}
                            >
                              A
                            </Button>
                            <Button
                              type="button"
                              size="icon"
                              variant={compareCandidateId === experiment.experiment_id ? "default" : "outline"}
                              aria-label={`Use ${experiment.title} as comparison B`}
                              onClick={() => setCompareCandidateId(experiment.experiment_id)}
                            >
                              B
                            </Button>
                            <Button
                              type="button"
                              size="sm"
                              variant="outline"
                              aria-label={`Open ${experiment.title}`}
                              onClick={() => void openExperiment(experiment.experiment_id)}
                            >
                              Open
                            </Button>
                          </div>
                          <div className="flex flex-wrap items-center gap-2">
                            <span className="w-14 text-xs text-muted-foreground">Manage</span>
                            <Button
                              type="button"
                              size="icon"
                              variant="outline"
                              aria-label={`Duplicate ${experiment.title}`}
                              onClick={() => void duplicateExperiment(experiment.experiment_id)}
                            >
                              <Copy className="size-4" />
                            </Button>
                            <Button
                              type="button"
                              size="icon"
                              variant="outline"
                              aria-label={experiment.archived ? `Restore ${experiment.title}` : `Archive ${experiment.title}`}
                              onClick={() => void setExperimentArchived(experiment, !experiment.archived)}
                            >
                              {experiment.archived ? <ArchiveRestore className="size-4" /> : <Archive className="size-4" />}
                            </Button>
                          </div>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function PaperRiskDashboard({
  summary,
  pnl,
}: {
  summary: PaperAccountSummaryResponse | null;
  pnl: PaperPnlSnapshotResponse | null;
}) {
  if (!summary) {
    return <p className="text-sm text-muted-foreground">Paper risk state is waiting for account data.</p>;
  }

  const snapshot = pnl?.snapshot ?? null;
  const latestAuditEvents = summary.recent_audit_events.slice(0, 5);
  return (
    <div className="grid gap-4">
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
        <MetricTile label="Cash" value={formatCurrency(summary.account.current_cash)} />
        <MetricTile label="Equity" value={snapshot ? formatCurrency(snapshot.account_equity) : "-"} />
        <MetricTile
          label="Unrealized"
          value={snapshot ? formatSignedCurrency(snapshot.total_unrealized_pnl) : "-"}
          tone={snapshot ? signedTone(snapshot.total_unrealized_pnl) : "neutral"}
        />
        <MetricTile
          label="Realized"
          value={snapshot ? formatSignedCurrency(snapshot.total_realized_pnl) : "-"}
          tone={snapshot ? signedTone(snapshot.total_realized_pnl) : "neutral"}
        />
        <MetricTile label="Price State" value={snapshot ? snapshot.price_state : "waiting"} />
      </div>
      <div className="grid gap-3 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)]">
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Position</TableHead>
                <TableHead>Qty</TableHead>
                <TableHead>Avg</TableHead>
                <TableHead>Reference</TableHead>
                <TableHead>Unrealized</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {summary.positions.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="text-sm text-muted-foreground">
                    No paper positions yet.
                  </TableCell>
                </TableRow>
              ) : (
                summary.positions.map((position) => {
                  const positionPnl = snapshot?.positions.find((row) => row.position_id === position.position_id) ?? null;
                  return (
                    <TableRow key={position.position_id}>
                      <TableCell className="min-w-[160px]">
                        <div className="font-medium">{position.symbol}</div>
                        <div className="text-xs text-muted-foreground">{position.asset_class}</div>
                      </TableCell>
                      <TableCell>{position.quantity}</TableCell>
                      <TableCell>{formatCurrency(position.average_price)}</TableCell>
                      <TableCell>
                        <div>{positionPnl?.reference_price ? formatCurrency(positionPnl.reference_price) : "-"}</div>
                        <Badge variant={positionPnl?.price_state === "fresh" ? "secondary" : "outline"}>
                          {positionPnl?.price_state ?? "missing"}
                        </Badge>
                      </TableCell>
                      <TableCell className={positionPnl?.unrealized_pnl && positionPnl.unrealized_pnl < 0 ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400"}>
                        {positionPnl?.unrealized_pnl === null || positionPnl?.unrealized_pnl === undefined
                          ? "-"
                          : formatSignedCurrency(positionPnl.unrealized_pnl)}
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>
        <div className="grid gap-3">
          <div className="rounded-md border bg-muted/20 p-3">
            <div className="flex items-center justify-between gap-2">
              <div className="text-sm font-medium">Recent Paper Flow</div>
              <Badge variant="outline">{summary.scope}</Badge>
            </div>
            <div className="mt-3 grid gap-2 text-sm">
              <MetricTile label="Recent intents" value={String(summary.recent_intents.length)} compact />
              <MetricTile label="Recent fills" value={String(summary.recent_fills.length)} compact />
            </div>
          </div>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Audit preview</TableHead>
                  <TableHead>Outcome</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {latestAuditEvents.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={2} className="text-sm text-muted-foreground">
                      No paper audit events yet.
                    </TableCell>
                  </TableRow>
                ) : (
                  latestAuditEvents.map((event) => (
                    <TableRow key={event.event_id}>
                      <TableCell className="min-w-[160px]">
                        <div className="font-medium">{event.reason_code}</div>
                        <div className="line-clamp-1 text-xs text-muted-foreground">{event.message}</div>
                      </TableCell>
                      <TableCell>{event.outcome}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </div>
      </div>
    </div>
  );
}

function WorkflowStep({ label, value, tone }: { label: string; value: string; tone: WorkflowStepTone }) {
  const indicator =
    tone === "complete" ? (
      <CheckCircle2 className="size-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
    ) : tone === "updating" ? (
      <RefreshCw className="size-4 shrink-0 text-blue-600 dark:text-blue-400" />
    ) : tone === "current" ? (
      <Activity className="size-4 shrink-0 text-blue-600 dark:text-blue-400" />
    ) : (
      <span className="size-4 shrink-0 rounded-full border border-muted-foreground/40" aria-hidden="true" />
    );
  return (
    <div className="flex min-h-16 items-center gap-3 rounded-md border bg-muted/20 p-3">
      {indicator}
      <div className="min-w-0">
        <div className="text-xs text-muted-foreground">{label}</div>
        <div className="mt-1 truncate text-sm font-medium">{value}</div>
      </div>
    </div>
  );
}

function RetryAlert({
  message,
  actionLabel,
  onRetry,
}: {
  message: string;
  actionLabel: string;
  onRetry: () => void;
}) {
  return (
    <Alert variant="destructive">
      <AlertDescription>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <span className="min-w-0">{message}</span>
          <Button type="button" size="sm" variant="outline" className="shrink-0" onClick={onRetry}>
            {actionLabel}
          </Button>
        </div>
      </AlertDescription>
    </Alert>
  );
}

function LoadingRows({ label, rows = 3 }: { label: string; rows?: number }) {
  return (
    <div className="grid gap-2" aria-label={label}>
      {Array.from({ length: rows }, (_, index) => (
        <div key={index} className="h-9 animate-pulse rounded-md bg-muted/40" />
      ))}
    </div>
  );
}

function ExperimentRailItem({
  experiment,
  selected,
  compareBaseSelected,
  compareCandidateSelected,
  onOpen,
  onDuplicate,
  onUseAsBase,
  onUseAsCandidate,
  onArchive,
  onReview,
}: {
  experiment: StrategyExperiment;
  selected: boolean;
  compareBaseSelected: boolean;
  compareCandidateSelected: boolean;
  onOpen: () => void;
  onDuplicate: () => void;
  onUseAsBase: () => void;
  onUseAsCandidate: () => void;
  onArchive: () => void;
  onReview: (status: StrategyExperimentReviewStatus) => void;
}) {
  return (
    <div
      className={
        selected
          ? "rounded-md border border-primary bg-primary/10 p-3"
          : "rounded-md border bg-muted/20 p-3"
      }
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="truncate text-sm font-medium">{experiment.title}</div>
          <div className="mt-1 text-xs text-muted-foreground">{formatTime(experiment.created_at)}</div>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-1">
          <Badge variant="outline">{String(experiment.parameters.fast_window ?? "-")}/{String(experiment.parameters.slow_window ?? "-")}</Badge>
          {experiment.archived ? <Badge variant="secondary">Archived</Badge> : null}
          <Badge variant={experiment.review_status === "candidate" ? "default" : "secondary"}>
            {reviewStatusLabel(experiment.review_status)}
          </Badge>
        </div>
      </div>
      <ExperimentMetadata experiment={experiment} />
      <div className="mt-3 grid grid-cols-2 gap-2">
        <MetricTile label="Final" value={formatCurrency(experiment.preview.backtest.final_equity)} compact />
        <MetricTile
          label="Return"
          value={`${experiment.preview.backtest.return_pct}%`}
          tone={experiment.preview.backtest.return_pct >= 0 ? "positive" : "negative"}
          compact
        />
      </div>
      <div className="mt-3 grid gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <span className="w-14 text-xs text-muted-foreground">Compare</span>
          <Button type="button" size="sm" variant="outline" onClick={onOpen}>
            Open
          </Button>
          <Button
            type="button"
            size="icon"
            variant={compareBaseSelected ? "default" : "outline"}
            aria-label={`Use ${experiment.title} as comparison A`}
            onClick={onUseAsBase}
          >
            A
          </Button>
          <Button
            type="button"
            size="icon"
            variant={compareCandidateSelected ? "default" : "outline"}
            aria-label={`Use ${experiment.title} as comparison B`}
            onClick={onUseAsCandidate}
          >
            B
          </Button>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="w-14 text-xs text-muted-foreground">Manage</span>
          <Button
            type="button"
            size="icon"
            variant="outline"
            aria-label={`Duplicate ${experiment.title}`}
            onClick={onDuplicate}
          >
            <Copy className="size-4" />
          </Button>
          <Button
            type="button"
            size="icon"
            variant="outline"
            aria-label={experiment.archived ? `Restore ${experiment.title}` : `Archive ${experiment.title}`}
            onClick={onArchive}
          >
            {experiment.archived ? <ArchiveRestore className="size-4" /> : <Archive className="size-4" />}
          </Button>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="w-14 text-xs text-muted-foreground">Review</span>
          <Button
            type="button"
            size="icon"
            variant={experiment.review_status === "reviewed" ? "default" : "outline"}
            aria-label={`Mark ${experiment.title} as reviewed`}
            onClick={() => onReview("reviewed")}
          >
            <CheckCircle2 className="size-4" />
          </Button>
          <Button
            type="button"
            size="icon"
            variant={experiment.review_status === "candidate" ? "default" : "outline"}
            aria-label={`Mark ${experiment.title} as candidate`}
            onClick={() => onReview("candidate")}
          >
            <BadgeCheck className="size-4" />
          </Button>
          <Button
            type="button"
            size="icon"
            variant={experiment.review_status === "rejected" ? "destructive" : "outline"}
            aria-label={`Reject ${experiment.title}`}
            onClick={() => onReview("rejected")}
          >
            <XCircle className="size-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}

function ExperimentMetadata({ experiment }: { experiment: StrategyExperiment }) {
  const tags = experiment.tags ?? [];
  if (tags.length === 0 && !experiment.notes) {
    return <div className="mt-2 text-xs text-muted-foreground">No tags or notes.</div>;
  }
  return (
    <div className="mt-2 grid gap-2">
      {tags.length > 0 ? (
        <div className="flex flex-wrap gap-1">
          {tags.map((tag) => (
            <Badge key={tag} variant="secondary" className="gap-1">
              <Tag className="size-3" />
              {tag}
            </Badge>
          ))}
        </div>
      ) : null}
      {experiment.notes ? (
        <div className="line-clamp-2 text-xs text-muted-foreground">{experiment.notes}</div>
      ) : null}
      <div className="text-xs text-muted-foreground">
        Review: <span className="font-medium text-foreground">{reviewStatusLabel(experiment.review_status)}</span>
      </div>
    </div>
  );
}

function CandidateBoardRow({
  candidate,
  onOpen,
  onUseAsBase,
  onUseAsCandidate,
  onReject,
  onArchive,
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
  return (
    <TableRow>
      <TableCell className="min-w-[220px]">
        <div className="font-medium">{candidate.title}</div>
        <div className="text-xs text-muted-foreground">
          {candidate.symbol} · {candidate.strategy_id}
        </div>
      </TableCell>
      <TableCell className="whitespace-nowrap">
        <div className={candidate.return_pct >= 0 ? "font-medium text-emerald-600 dark:text-emerald-400" : "font-medium text-red-600 dark:text-red-400"}>
          {candidate.return_pct}%
        </div>
        <div className="text-xs text-muted-foreground">{formatCurrency(candidate.final_equity)}</div>
      </TableCell>
      <TableCell className="whitespace-nowrap">
        {candidate.trade_count}
        <div className="text-xs text-muted-foreground">{candidate.marker_count} markers</div>
      </TableCell>
      <TableCell className="min-w-[160px]">
        <ChecklistSummary checklist={candidate.review_checklist} />
      </TableCell>
      <TableCell className="min-w-[180px]">
        <div className="flex flex-wrap gap-1">
          {candidate.tags.length > 0 ? candidate.tags.map((tag) => (
            <Badge key={tag} variant="secondary" className="gap-1">
              <Tag className="size-3" />
              {tag}
            </Badge>
          )) : <span className="text-xs text-muted-foreground">No tags</span>}
        </div>
      </TableCell>
      <TableCell>
        <div className="grid gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <span className="w-14 text-xs text-muted-foreground">Compare</span>
            <Button type="button" size="sm" variant="outline" onClick={onOpen}>
              Open
            </Button>
            <Button type="button" size="icon" variant="outline" aria-label={`Use ${candidate.title} as comparison A`} onClick={onUseAsBase}>
              A
            </Button>
            <Button type="button" size="icon" variant="outline" aria-label={`Use ${candidate.title} as comparison B`} onClick={onUseAsCandidate}>
              B
            </Button>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <span className="w-14 text-xs text-muted-foreground">Review</span>
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
            <Button
              type="button"
              size="icon"
              variant="outline"
              aria-label={`Archive ${candidate.title}`}
              onClick={onArchive}
            >
              <Archive className="size-4" />
            </Button>
            <Button
              type="button"
              size="icon"
              variant="destructive"
              aria-label={`Reject ${candidate.title}`}
              onClick={onReject}
            >
              <XCircle className="size-4" />
            </Button>
          </div>
        </div>
      </TableCell>
    </TableRow>
  );
}

function ChecklistSummary({ checklist }: { checklist: Record<string, boolean> }) {
  const entries = Object.entries(checklist);
  if (entries.length === 0) {
    return <span className="text-xs text-muted-foreground">No checklist</span>;
  }
  const completeCount = entries.filter(([, value]) => value).length;
  return (
    <div className="text-xs text-muted-foreground">
      <div className="font-medium text-foreground">{completeCount}/{entries.length} checked</div>
      <div className="mt-1 line-clamp-2">
        {entries.filter(([, value]) => value).map(([key]) => key.split("_").join(" ")).join(", ")}
      </div>
    </div>
  );
}

function SignalRowsTable({ preview }: { preview: StrategyPreviewResponse | null }) {
  const rows = preview?.signals.slice(-10) ?? [];
  if (rows.length === 0) {
    return <p className="text-sm text-muted-foreground">Waiting for signal rows.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Time</TableHead>
            <TableHead>Close</TableHead>
            <TableHead>Signal</TableHead>
            <TableHead>Position</TableHead>
            <TableHead>Reason</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((row) => (
            <TableRow key={`${row.timestamp}-${row.signal}-${row.position}`}>
              <TableCell className="whitespace-nowrap">{formatTime(row.timestamp)}</TableCell>
              <TableCell>{row.close.toFixed(2)}</TableCell>
              <TableCell>
                <Badge variant={row.signal === 1 ? "default" : row.signal === -1 ? "destructive" : "secondary"}>
                  {signalLabel(row.signal)}
                </Badge>
              </TableCell>
              <TableCell>{row.position}</TableCell>
              <TableCell className="min-w-[220px] text-muted-foreground">{row.reason}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}

function ExperimentComparisonPanel({
  comparison,
  comparisonLoading,
  comparisonError,
  baseTitle,
  candidateTitle,
  onRetry,
}: {
  comparison: StrategyExperimentComparison | null;
  comparisonLoading: boolean;
  comparisonError: string | null;
  baseTitle: string | null;
  candidateTitle: string | null;
  onRetry: () => void;
}) {
  if (!baseTitle && !candidateTitle && !comparisonError) {
    return null;
  }

  return (
    <div className="mb-4 rounded-md border bg-muted/20 p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-sm font-medium">
          <GitCompareArrows className="size-4" />
          Experiment Comparison
        </div>
        <Badge variant="outline">research_only</Badge>
      </div>
      <div className="mb-3 grid gap-2 text-sm md:grid-cols-2">
        <div className="rounded-md border bg-background p-3">
          <div className="text-xs text-muted-foreground">A</div>
          <div className="mt-1 truncate font-medium">{baseTitle ?? "Select baseline"}</div>
        </div>
        <div className="rounded-md border bg-background p-3">
          <div className="text-xs text-muted-foreground">B</div>
          <div className="mt-1 truncate font-medium">{candidateTitle ?? "Select candidate"}</div>
        </div>
      </div>
      {comparisonError ? (
        <RetryAlert message={comparisonError} actionLabel="Retry comparison" onRetry={onRetry} />
      ) : comparisonLoading ? (
        <p className="text-sm text-muted-foreground">Comparing experiments.</p>
      ) : comparison ? (
        <div className="grid gap-3">
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
            <MetricTile label="Final Delta" value={formatSignedCurrency(comparison.deltas.final_equity)} />
            <MetricTile label="Return Delta" value={formatSignedPercent(comparison.deltas.return_pct)} />
            <MetricTile label="Trades Delta" value={formatSignedNumber(comparison.deltas.trade_count)} />
            <MetricTile label="Markers Delta" value={formatSignedNumber(comparison.deltas.marker_count)} />
            <MetricTile label="Signals Delta" value={formatSignedNumber(comparison.deltas.signal_count)} />
          </div>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Parameter</TableHead>
                  <TableHead>A</TableHead>
                  <TableHead>B</TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Object.entries(comparison.parameter_deltas).map(([parameter, delta]) => (
                  <TableRow key={parameter}>
                    <TableCell className="font-medium">{parameter}</TableCell>
                    <TableCell>{String(delta.base ?? "-")}</TableCell>
                    <TableCell>{String(delta.candidate ?? "-")}</TableCell>
                    <TableCell>
                      <Badge variant={delta.changed ? "default" : "secondary"}>
                        {delta.changed ? "Changed" : "Same"}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">Select A and B from saved experiments.</p>
      )}
    </div>
  );
}

function StrategyOverlayChart({
  preview,
  bars,
  fastWindow,
  slowWindow,
}: {
  preview: StrategyPreviewResponse | null;
  bars: MarketBar[];
  fastWindow: number;
  slowWindow: number;
}) {
  const chartContainerRef = useRef<HTMLDivElement | null>(null);
  const candleData = useMemo(() => toStrategyCandles(bars), [bars]);
  const volumeData = useMemo(() => toStrategyVolume(bars), [bars]);
  const markers = useMemo(() => toStrategyMarkers(preview), [preview]);
  const fastMa = useMemo(() => toMovingAverageData(candleData, fastWindow), [candleData, fastWindow]);
  const slowMa = useMemo(() => toMovingAverageData(candleData, slowWindow), [candleData, slowWindow]);
  const chartSummaryId = useId();
  const chartSummary = preview ? getStrategyChartSummary(preview, candleData, markers, fastWindow, slowWindow) : "";

  useEffect(() => {
    const container = chartContainerRef.current;
    if (!container || candleData.length === 0) return;

    const chart = createChart(container, {
      autoSize: true,
      height: 360,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#64748b",
      },
      grid: {
        horzLines: { color: "rgba(148, 163, 184, 0.22)" },
        vertLines: { color: "rgba(148, 163, 184, 0.16)" },
      },
      rightPriceScale: {
        borderColor: "rgba(148, 163, 184, 0.24)",
      },
      timeScale: {
        borderColor: "rgba(148, 163, 184, 0.24)",
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: {
        mode: 1,
      },
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#16a34a",
      downColor: "#dc2626",
      borderUpColor: "#16a34a",
      borderDownColor: "#dc2626",
      wickUpColor: "#16a34a",
      wickDownColor: "#dc2626",
    });
    candleSeries.setData(candleData);
    createSeriesMarkers(candleSeries, markers);

    const fastSeries = chart.addSeries(LineSeries, {
      color: "#2563eb",
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
      title: `Fast ${fastWindow}`,
    });
    fastSeries.setData(fastMa);

    const slowSeries = chart.addSeries(LineSeries, {
      color: "#7c3aed",
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
      title: `Slow ${slowWindow}`,
    });
    slowSeries.setData(slowMa);

    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: "#64748b",
      priceFormat: { type: "volume" },
      priceScaleId: "volume",
    });
    volumeSeries.setData(volumeData);
    chart.priceScale("volume").applyOptions({
      scaleMargins: {
        top: 0.78,
        bottom: 0,
      },
    });
    chart.timeScale().fitContent();

    return () => {
      chart.remove();
    };
  }, [candleData, fastMa, fastWindow, markers, slowMa, slowWindow, volumeData]);

  if (!preview || candleData.length === 0) {
    return (
      <div className="grid h-[360px] place-items-center rounded-md border bg-muted/30 text-sm text-muted-foreground">
        Waiting for strategy preview.
      </div>
    );
  }

  return (
    <figure className="overflow-hidden rounded-md border bg-background">
      <div
        ref={chartContainerRef}
        className="h-[360px] min-w-0"
        role="img"
        aria-label={`${preview.overlay.symbol} strategy candlestick overlay`}
        aria-describedby={chartSummaryId}
      />
      <figcaption id={chartSummaryId} className="sr-only">
        {chartSummary}
      </figcaption>
    </figure>
  );
}

function getStrategyChartSummary(
  preview: StrategyPreviewResponse,
  candleData: CandlestickData<Time>[],
  markers: SeriesMarker<Time>[],
  fastWindow: number,
  slowWindow: number,
) {
  const firstBar = candleData[0];
  const lastBar = candleData[candleData.length - 1];
  const buyMarkers = markers.filter((marker) => marker.text === "BUY").length;
  const exitMarkers = markers.filter((marker) => marker.text === "EXIT").length;
  const lastSignal = preview.signals[preview.signals.length - 1];
  const lastSignalLabel = lastSignal ? signalLabel(lastSignal.signal) : "none";

  return [
    `${preview.overlay.symbol} research-only candlestick chart with ${candleData.length} bars.`,
    `Fast moving average window ${fastWindow}; slow moving average window ${slowWindow}.`,
    `First close ${firstBar ? formatCurrency(firstBar.close) : "-"}; latest close ${lastBar ? formatCurrency(lastBar.close) : "-"}.`,
    `${buyMarkers} buy markers and ${exitMarkers} exit markers are shown.`,
    `Latest signal ${lastSignalLabel}; backtest return ${preview.backtest.return_pct}%; final equity ${formatCurrency(preview.backtest.final_equity)} across ${preview.backtest.trades.length} trades.`,
  ].join(" ");
}

function MetricTile({
  label,
  value,
  tone = "neutral",
  compact = false,
}: {
  label: string;
  value: string;
  tone?: "neutral" | "positive" | "negative";
  compact?: boolean;
}) {
  const toneClass =
    tone === "positive"
      ? "text-emerald-600 dark:text-emerald-400"
      : tone === "negative"
        ? "text-red-600 dark:text-red-400"
        : "text-foreground";
  return (
    <div className={compact ? "rounded-md border bg-background/60 p-2" : "rounded-md border bg-muted/20 p-3"}>
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className={`${compact ? "text-sm" : "text-lg"} mt-1 truncate font-semibold ${toneClass}`}>{value}</div>
    </div>
  );
}

type PaperActionState = {
  canRiskCheck: boolean;
  canApprove: boolean;
  canReject: boolean;
  canSubmit: boolean;
  canCancel: boolean;
  nextStep: string;
  blocker: string;
};

function getPaperDisabledReasons(
  paperIntent: PaperIntentResponse,
  paperActionState: PaperActionState,
): Array<{ label: string; reason: string }> {
  const status = paperIntent.intent.status;
  const riskResult = paperIntent.latest_risk_decision?.result ?? null;
  const reasons: Array<{ label: string; reason: string }> = [];
  if (!paperActionState.canRiskCheck) {
    reasons.push({ label: "Run RiskGuard", reason: paperActionState.blocker });
  }
  if (!paperActionState.canApprove) {
    const reason =
      status === "approved_for_paper"
        ? "This paper intent has already been approved."
        : status === "paper_submitted" || status === "paper_filled" || status === "paper_cancelled"
          ? "This paper intent is past the human review step."
          : riskResult === "reject" || status === "risk_rejected"
            ? "RiskGuard rejected this paper intent."
            : "RiskGuard must pass before human approval is available.";
    reasons.push({ label: "Approve Paper", reason });
  }
  if (!paperActionState.canReject) {
    const reason =
      status === "draft"
        ? "Run RiskGuard before rejecting during review."
        : status === "paper_submitted" || status === "paper_filled" || status === "paper_cancelled"
          ? "This paper intent is past the human review step."
          : "There is no reviewed paper intent to reject yet.";
    reasons.push({ label: "Reject Paper", reason });
  }
  if (!paperActionState.canSubmit) {
    const reason =
      status === "paper_submitted" || status === "paper_filled" || status === "paper_cancelled"
        ? "This paper intent has already left the submit step."
        : "Human approval must unlock local paper submission first.";
    reasons.push({ label: "Paper Submit", reason });
  }
  if (!paperActionState.canCancel) {
    reasons.push({ label: "Cancel Paper", reason: "Terminal paper intents can no longer be cancelled." });
  }
  return reasons;
}

function getPaperActionState(paperIntent: PaperIntentResponse): PaperActionState {
  const status = paperIntent.intent.status;
  const terminal = status === "paper_filled" || status === "paper_cancelled";
  const riskResult = paperIntent.latest_risk_decision?.result ?? null;
  const canApprove = status === "awaiting_review" && riskResult === "pass";
  const canSubmit = status === "approved_for_paper";
  const canCancel = !terminal;

  if (status === "paper_filled") {
    return {
      canRiskCheck: false,
      canApprove: false,
      canReject: false,
      canSubmit: false,
      canCancel: false,
      nextStep: "Paper simulation is complete.",
      blocker: "This intent was filled locally and can no longer be changed.",
    };
  }

  if (status === "paper_cancelled") {
    return {
      canRiskCheck: false,
      canApprove: false,
      canReject: false,
      canSubmit: false,
      canCancel: false,
      nextStep: "Paper intent is cancelled.",
      blocker: "Create a new paper draft from a candidate to continue.",
    };
  }

  if (riskResult === "reject" || status === "risk_rejected") {
    return {
      canRiskCheck: true,
      canApprove: false,
      canReject: true,
      canSubmit: false,
      canCancel,
      nextStep: "RiskGuard rejected this paper intent.",
      blocker: "Review the reason codes, reject or cancel this paper intent, or adjust the candidate before creating a new draft.",
    };
  }

  if (status === "paper_submitted") {
    return {
      canRiskCheck: false,
      canApprove: false,
      canReject: false,
      canSubmit: false,
      canCancel,
      nextStep: "Submitted to the local paper adapter.",
      blocker: "Wait for the simulated fill result or cancel if this paper intent should not continue.",
    };
  }

  if (canSubmit) {
    return {
      canRiskCheck: true,
      canApprove: false,
      canReject: true,
      canSubmit: true,
      canCancel,
      nextStep: "Approved for paper simulation.",
      blocker: "Paper Submit will only use the local deterministic paper adapter; no broker or live account is involved.",
    };
  }

  if (canApprove) {
    return {
      canRiskCheck: true,
      canApprove: true,
      canReject: true,
      canSubmit: false,
      canCancel,
      nextStep: "Human approval is required before paper submit.",
      blocker: "Approve Paper enables the local paper simulation submit step.",
    };
  }

  return {
    canRiskCheck: true,
    canApprove: false,
    canReject: status !== "draft",
    canSubmit: false,
    canCancel,
    nextStep: "Run RiskGuard before human paper approval.",
    blocker: "Approval and paper submit stay locked until RiskGuard returns a pass decision.",
  };
}

function paperIntentStatusLabel(status: PaperIntentResponse["intent"]["status"]) {
  if (status === "risk_rejected") return "Risk rejected";
  if (status === "awaiting_review") return "Awaiting review";
  if (status === "approved_for_paper") return "Approved for paper";
  if (status === "paper_submitted") return "Paper submitted";
  if (status === "paper_filled") return "Paper filled";
  if (status === "paper_cancelled") return "Paper cancelled";
  return "Draft";
}

function paperRetryActionLabel(paperIntent: PaperIntentResponse | null, action: PaperRetryAction) {
  if (!paperIntent || action === "loadAccounts" || action === "createDraft") return "Reload accounts";
  if (action === "riskCheck") return "Run RiskGuard";
  if (action === "approve") return "Approve Paper";
  if (action === "reject") return "Reject Paper";
  if (action === "submit") return "Paper Submit";
  return "Cancel Paper";
}

function signalTone(signal: number): "neutral" | "positive" | "negative" {
  if (signal === 1) return "positive";
  if (signal === -1) return "negative";
  return "neutral";
}

function parseTags(value: string): string[] {
  const tags = value
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
  return Array.from(new Set(tags)).slice(0, 12);
}

function reviewStatusLabel(status: StrategyExperimentReviewStatus): string {
  if (status === "candidate") return "Candidate";
  if (status === "reviewed") return "Reviewed";
  if (status === "rejected") return "Rejected";
  return "Draft";
}

function buildReviewChecklist(status: StrategyExperimentReviewStatus): Record<string, boolean> {
  if (status === "candidate") {
    return {
      data_range_reviewed: true,
      parameters_reviewed: true,
      backtest_reviewed: true,
      risk_notes_added: true,
      human_reviewed: true,
    };
  }
  if (status === "reviewed") {
    return {
      data_range_reviewed: true,
      parameters_reviewed: true,
      backtest_reviewed: true,
      risk_notes_added: false,
      human_reviewed: true,
    };
  }
  return {};
}

function toStrategyCandles(bars: MarketBar[]): CandlestickData<Time>[] {
  const byTime = new Map<number, CandlestickData<Time>>();
  for (const bar of bars) {
    const time = Math.floor(new Date(bar.timestamp).getTime() / 1000);
    byTime.set(time, {
      time: time as Time,
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
    });
  }
  return Array.from(byTime.values()).sort((left, right) => Number(left.time) - Number(right.time));
}

function toStrategyVolume(bars: MarketBar[]): HistogramData<Time>[] {
  const byTime = new Map<number, HistogramData<Time>>();
  for (const bar of bars) {
    const time = Math.floor(new Date(bar.timestamp).getTime() / 1000);
    byTime.set(time, {
      time: time as Time,
      value: bar.volume,
      color: bar.close >= bar.open ? "rgba(22, 163, 74, 0.28)" : "rgba(220, 38, 38, 0.28)",
    });
  }
  return Array.from(byTime.values()).sort((left, right) => Number(left.time) - Number(right.time));
}

function toStrategyMarkers(preview: StrategyPreviewResponse | null): SeriesMarker<Time>[] {
  if (!preview) return [];
  return preview.overlay.markers
    .map((marker): SeriesMarker<Time> => ({
      time: Math.floor(new Date(marker.time).getTime() / 1000) as Time,
      position: marker.position,
      shape: marker.shape,
      color: marker.color,
      text: marker.shape === "arrowUp" ? "BUY" : "EXIT",
      size: 1.1,
    }))
    .sort((left, right) => Number(left.time) - Number(right.time));
}

function toMovingAverageData(data: CandlestickData<Time>[], period: number): LineData<Time>[] {
  if (period <= 0) return [];
  return data
    .map((bar, index) => {
      if (index + 1 < period) return null;
      const window = data.slice(index + 1 - period, index + 1);
      const value = window.reduce((sum, item) => sum + item.close, 0) / period;
      return {
        time: bar.time,
        value,
      };
    })
    .filter((item): item is LineData<Time> => item !== null);
}

function buildPaperReferencePrices(
  summary: PaperAccountSummaryResponse,
  bars: MarketBar[],
): PaperReferencePrice[] {
  const latestBySymbol = new Map<string, MarketBar>();
  for (const bar of bars) {
    const key = bar.symbol.toUpperCase();
    const existing = latestBySymbol.get(key);
    if (!existing || new Date(bar.timestamp).getTime() > new Date(existing.timestamp).getTime()) {
      latestBySymbol.set(key, bar);
    }
  }
  return summary.positions
    .map((position) => {
      const bar = latestBySymbol.get(position.symbol.toUpperCase());
      if (!bar) return null;
      return {
        symbol: position.symbol,
        asset_class: position.asset_class,
        price: bar.close,
        priced_at: bar.timestamp,
      };
    })
    .filter((price): price is PaperReferencePrice => price !== null);
}

function signalLabel(signal: number) {
  if (signal === 1) return "BUY";
  if (signal === -1) return "EXIT";
  return "HOLD";
}

function signedTone(value: number): "neutral" | "positive" | "negative" {
  if (value > 0) return "positive";
  if (value < 0) return "negative";
  return "neutral";
}

function formatCurrency(value?: number) {
  if (value === undefined) return "-";
  return `$${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

function formatSignedCurrency(value: number) {
  const sign = value > 0 ? "+" : "";
  return `${sign}${formatCurrency(value)}`;
}

function formatSignedNumber(value: number) {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toLocaleString()}`;
}

function formatSignedPercent(value: number) {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toLocaleString(undefined, { maximumFractionDigits: 4 })}%`;
}

function formatTime(value: string) {
  return new Date(value).toLocaleString(undefined, {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
