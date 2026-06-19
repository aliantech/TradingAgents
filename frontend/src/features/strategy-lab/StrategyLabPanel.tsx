import { useEffect, useMemo, useRef, useState } from "react";
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
  ChartNoAxesCombined,
  CheckCircle2,
  Copy,
  FileText,
  FlaskConical,
  GitCompareArrows,
  History,
  Layers3,
  ListChecks,
  RefreshCw,
  Save,
  SlidersHorizontal,
  Tag,
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
  duplicateStrategyExperiment,
  getStrategyExperiment,
  listStrategyCatalog,
  listStrategyExperiments,
  previewSignalStrategy,
  saveStrategyExperiment,
  updateStrategyExperiment,
  type MarketBar,
  type ReportListItem,
  type StrategyCatalogItem,
  type StrategyExperimentComparison,
  type StrategyExperiment,
  type StrategyPreviewResponse,
} from "@/lib/api";

type StrategyLabPanelProps = {
  symbol: string;
  bars: MarketBar[];
  latestReport: ReportListItem | null;
  onRefreshMarket: () => void;
};

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
  const [showArchived, setShowArchived] = useState(false);
  const [compareBaseId, setCompareBaseId] = useState<string | null>(null);
  const [compareCandidateId, setCompareCandidateId] = useState<string | null>(null);
  const [comparison, setComparison] = useState<StrategyExperimentComparison | null>(null);
  const [comparisonLoading, setComparisonLoading] = useState(false);
  const [comparisonError, setComparisonError] = useState<string | null>(null);
  const previewBars = useMemo(() => bars.slice(-80), [bars]);
  const canPreview = previewBars.length >= Math.max(fastWindow, slowWindow);
  const selectedStrategy = strategies.find((strategy) => strategy.strategy_id === selectedStrategyId) ?? null;

  useEffect(() => {
    void loadCatalog();
  }, []);

  useEffect(() => {
    void loadExperiments();
  }, [symbol, showArchived, tagFilter]);

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
    } catch (caught) {
      setExperimentsError(caught instanceof Error ? caught.message : "Strategy experiment archive update failed.");
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

  const latestSignal = preview?.signals[preview.signals.length - 1];
  const tradeCount = preview?.backtest.trades.length ?? 0;
  const markerCount = preview?.overlay.markers.length ?? 0;
  const activeExperiment = experiments.find((experiment) => experiment.experiment_id === activeExperimentId);
  const buyCount = preview?.signals.filter((row) => row.signal === 1).length ?? 0;
  const exitCount = preview?.signals.filter((row) => row.signal === -1).length ?? 0;
  const workflowSteps = [
    { label: "Catalog", value: selectedStrategy?.name ?? "Loading" },
    { label: "Preview", value: loading ? "Updating" : canPreview ? "Live" : "Waiting" },
    { label: "Experiment", value: activeExperiment ? "Opened" : "Draft" },
    { label: "Report", value: latestReport ? "Linked" : "Unlinked" },
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
            <WorkflowStep key={step.label} label={step.label} value={step.value} />
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
                <Alert variant="destructive">
                  <AlertDescription>{catalogError}</AlertDescription>
                </Alert>
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
                <Alert variant="destructive">
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
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
              {experimentsError ? (
                <Alert variant="destructive">
                  <AlertDescription>{experimentsError}</AlertDescription>
                </Alert>
              ) : null}
              {experimentsLoading ? (
                <p className="text-sm text-muted-foreground">Loading experiments.</p>
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
          />
        </aside>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base">
            <Layers3 className="size-4" />
            Saved Experiment Table
          </CardTitle>
        </CardHeader>
        <CardContent>
          {experimentsLoading ? (
            <p className="text-sm text-muted-foreground">Loading experiments.</p>
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
                    <TableHead className="w-[230px]">Actions</TableHead>
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
                        <div className="flex flex-wrap gap-2">
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

function WorkflowStep({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex min-h-16 items-center gap-3 rounded-md border bg-muted/20 p-3">
      <CheckCircle2 className="size-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
      <div className="min-w-0">
        <div className="text-xs text-muted-foreground">{label}</div>
        <div className="mt-1 truncate text-sm font-medium">{value}</div>
      </div>
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
      <div className="mt-3 flex flex-wrap gap-2">
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
}: {
  comparison: StrategyExperimentComparison | null;
  comparisonLoading: boolean;
  comparisonError: string | null;
  baseTitle: string | null;
  candidateTitle: string | null;
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
        <Alert variant="destructive">
          <AlertDescription>{comparisonError}</AlertDescription>
        </Alert>
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
    <div className="overflow-hidden rounded-md border bg-background">
      <div ref={chartContainerRef} className="h-[360px] min-w-0" aria-label={`${preview.overlay.symbol} strategy candlestick overlay`} />
    </div>
  );
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

function signalLabel(signal: number) {
  if (signal === 1) return "BUY";
  if (signal === -1) return "EXIT";
  return "HOLD";
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
