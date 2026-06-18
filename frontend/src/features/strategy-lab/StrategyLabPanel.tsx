import { useEffect, useMemo, useState } from "react";
import { Activity, ChartNoAxesCombined, Copy, FileText, FlaskConical, GitCompareArrows, History, RefreshCw, Save } from "lucide-react";

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
import {
  compareStrategyExperiments,
  duplicateStrategyExperiment,
  getStrategyExperiment,
  listStrategyCatalog,
  listStrategyExperiments,
  previewSignalStrategy,
  saveStrategyExperiment,
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
  }, [symbol]);

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
      const response = await listStrategyExperiments(symbol);
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

  return (
    <div className="grid gap-4">
      <div className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <FlaskConical className="size-5" />
                {selectedStrategy?.name ?? "Strategy Lab"}
              </CardTitle>
              <Badge variant="outline">research_only</Badge>
            </div>
          </CardHeader>
          <CardContent className="grid gap-4">
            <div className="rounded-md border bg-muted/20 p-3 text-sm">
              <div className="text-xs text-muted-foreground">Strategy</div>
              <div className="mt-1 font-medium">{selectedStrategy?.strategy_id ?? selectedStrategyId}</div>
              <div className="mt-1 text-xs text-muted-foreground">
                {selectedStrategy?.description ?? "Loading strategy catalog."}
              </div>
            </div>
            {catalogError ? (
              <Alert variant="destructive">
                <AlertDescription>{catalogError}</AlertDescription>
              </Alert>
            ) : null}
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
            <div className="grid grid-cols-2 gap-2">
              <MetricTile label="Bars" value={previewBars.length.toString()} />
              <MetricTile label="Markers" value={markerCount.toString()} />
              <MetricTile label="Trades" value={tradeCount.toString()} />
              <MetricTile label="Signal" value={signalLabel(latestSignal?.signal ?? 0)} />
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Button type="button" variant="outline" onClick={onRefreshMarket} className="gap-2">
                <RefreshCw className="size-4" />
                Refresh Bars
              </Button>
              <Button type="button" onClick={saveCurrentExperiment} disabled={!preview || saving} className="gap-2">
                <Save className="size-4" />
                {saving ? "Saving" : "Save"}
              </Button>
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
          <CardHeader>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <ChartNoAxesCombined className="size-5" />
                {symbol.toUpperCase()} Overlay
              </CardTitle>
              <Badge variant={loading ? "secondary" : "default"}>{loading ? "Updating" : "Live Preview"}</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <StrategyOverlayChart preview={preview} />
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Activity className="size-4" />
              Backtest
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-2">
            <MetricTile label="Initial" value={formatCurrency(preview?.backtest.initial_equity)} />
            <MetricTile label="Final" value={formatCurrency(preview?.backtest.final_equity)} />
            <MetricTile label="Return" value={`${preview?.backtest.return_pct ?? 0}%`} />
          </CardContent>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader>
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

      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <History className="size-4" />
              Experiment History
            </CardTitle>
            <Button type="button" variant="outline" size="sm" onClick={() => void loadExperiments()} className="gap-2">
              <RefreshCw className="size-4" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {experimentsError ? (
            <Alert variant="destructive" className="mb-3">
              <AlertDescription>{experimentsError}</AlertDescription>
            </Alert>
          ) : null}
          <ExperimentComparisonPanel
            comparison={comparison}
            comparisonLoading={comparisonLoading}
            comparisonError={comparisonError}
            baseTitle={experiments.find((experiment) => experiment.experiment_id === compareBaseId)?.title ?? null}
            candidateTitle={experiments.find((experiment) => experiment.experiment_id === compareCandidateId)?.title ?? null}
          />
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

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Signal Rows</CardTitle>
        </CardHeader>
        <CardContent>
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
                {(preview?.signals.slice(-12) ?? []).map((row) => (
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
        </CardContent>
      </Card>
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

function StrategyOverlayChart({ preview }: { preview: StrategyPreviewResponse | null }) {
  const width = 820;
  const height = 300;
  if (!preview || preview.overlay.price_series.length === 0) {
    return (
      <div className="grid h-[300px] place-items-center rounded-md border bg-muted/30 text-sm text-muted-foreground">
        Waiting for strategy preview.
      </div>
    );
  }
  const points = preview.overlay.price_series;
  const values = points.map((point) => point.value);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = Math.max(max - min, 1);
  const x = (index: number) => 24 + (index / Math.max(points.length - 1, 1)) * (width - 48);
  const y = (value: number) => 24 + ((max - value) / span) * (height - 48);
  const path = points.map((point, index) => `${index === 0 ? "M" : "L"} ${x(index)} ${y(point.value)}`).join(" ");
  const markerByTime = new Map(preview.overlay.markers.map((marker) => [marker.time, marker]));

  return (
    <div className="overflow-hidden rounded-md border bg-background">
      <svg viewBox={`0 0 ${width} ${height}`} className="h-[300px] w-full" role="img" aria-label="SignalStrategy overlay">
        <rect x="0" y="0" width={width} height={height} fill="transparent" />
        <path d={path} fill="none" stroke="#2563eb" strokeWidth="3" />
        {points.map((point, index) => {
          const marker = markerByTime.get(point.time);
          if (!marker) return null;
          return (
            <g key={point.time}>
              <circle cx={x(index)} cy={y(point.value)} r="7" fill={marker.color} />
              <text x={x(index)} y={marker.shape === "arrowUp" ? y(point.value) - 14 : y(point.value) + 24} textAnchor="middle" className="fill-foreground text-[12px]">
                {marker.shape === "arrowUp" ? "BUY" : "EXIT"}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function MetricTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border bg-muted/20 p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="mt-1 truncate text-lg font-semibold">{value}</div>
    </div>
  );
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
