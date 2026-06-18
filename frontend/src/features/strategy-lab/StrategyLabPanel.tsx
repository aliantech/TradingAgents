import { useEffect, useMemo, useState } from "react";
import { Activity, ChartNoAxesCombined, FileText, FlaskConical, RefreshCw } from "lucide-react";

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
  previewSignalStrategy,
  type MarketBar,
  type ReportListItem,
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
  const [fastWindow, setFastWindow] = useState(2);
  const [slowWindow, setSlowWindow] = useState(3);
  const [initialEquity, setInitialEquity] = useState(10_000);
  const [preview, setPreview] = useState<StrategyPreviewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const previewBars = useMemo(() => bars.slice(-80), [bars]);
  const canPreview = previewBars.length >= Math.max(fastWindow, slowWindow);

  useEffect(() => {
    if (!canPreview) {
      setPreview(null);
      return;
    }
    const timeout = window.setTimeout(() => {
      void loadPreview();
    }, 180);
    return () => window.clearTimeout(timeout);
  }, [symbol, fastWindow, slowWindow, initialEquity, previewBars, canPreview]);

  async function loadPreview() {
    setLoading(true);
    setError(null);
    try {
      const response = await previewSignalStrategy({
        symbol,
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

  const latestSignal = preview?.signals[preview.signals.length - 1];
  const tradeCount = preview?.backtest.trades.length ?? 0;
  const markerCount = preview?.overlay.markers.length ?? 0;

  return (
    <div className="grid gap-4">
      <div className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-3">
              <CardTitle className="flex items-center gap-2 text-lg">
                <FlaskConical className="size-5" />
                SignalStrategy
              </CardTitle>
              <Badge variant="outline">research_only</Badge>
            </div>
          </CardHeader>
          <CardContent className="grid gap-4">
            <label className="grid gap-1">
              <span className="text-xs text-muted-foreground">Fast Window</span>
              <Input
                type="number"
                min={1}
                max={100}
                value={fastWindow}
                onChange={(event) => {
                  const nextFastWindow = Number(event.target.value);
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
                onChange={(event) => setSlowWindow(Math.max(Number(event.target.value), fastWindow))}
              />
            </label>
            <label className="grid gap-1">
              <span className="text-xs text-muted-foreground">Initial Equity</span>
              <Input
                type="number"
                min={1}
                step={100}
                value={initialEquity}
                onChange={(event) => setInitialEquity(Number(event.target.value))}
              />
            </label>
            <div className="grid grid-cols-2 gap-2">
              <MetricTile label="Bars" value={previewBars.length.toString()} />
              <MetricTile label="Markers" value={markerCount.toString()} />
              <MetricTile label="Trades" value={tradeCount.toString()} />
              <MetricTile label="Signal" value={signalLabel(latestSignal?.signal ?? 0)} />
            </div>
            <Button type="button" variant="outline" onClick={onRefreshMarket} className="gap-2">
              <RefreshCw className="size-4" />
              Refresh Bars
            </Button>
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

function formatTime(value: string) {
  return new Date(value).toLocaleString(undefined, {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
