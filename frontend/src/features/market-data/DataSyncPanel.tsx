import type {
  ProviderReadiness,
  ProviderSyncHealth,
  ProviderSyncRunItem,
  ProviderSyncSummary,
  ProviderSyncSummaryGroup,
} from "../../lib/api";
import { useTranslation } from "react-i18next";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardAction, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { MetricCard, StatusCard } from "@/components/workbench/metric-card";

type DataSyncPanelProps = {
  runs: ProviderSyncRunItem[];
  summary: ProviderSyncSummary | null;
  groups: ProviderSyncSummaryGroup[];
  health: ProviderSyncHealth | null;
  readiness: ProviderReadiness | null;
  loading: boolean;
  syncing: boolean;
  error: string | null;
  providerFilter: string;
  syncTypeFilter: string;
  startedAfterFilter: string;
  startedBeforeFilter: string;
  onProviderFilterChange: (provider: string) => void;
  onSyncTypeFilterChange: (syncType: string) => void;
  onStartedAfterFilterChange: (startedAfter: string) => void;
  onStartedBeforeFilterChange: (startedBefore: string) => void;
  onConfigureProvider: () => void;
  onRefresh: () => void;
  onSyncSample: () => void;
};

export function DataSyncPanel({
  runs,
  summary,
  groups,
  health,
  readiness,
  loading,
  syncing,
  error,
  providerFilter,
  syncTypeFilter,
  startedAfterFilter,
  startedBeforeFilter,
  onProviderFilterChange,
  onSyncTypeFilterChange,
  onStartedAfterFilterChange,
  onStartedBeforeFilterChange,
  onConfigureProvider,
  onRefresh,
  onSyncSample,
}: DataSyncPanelProps) {
  const { t } = useTranslation();
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("market.syncTitle")}</CardTitle>
        <CardAction className="flex gap-2">
          <Button type="button" variant="outline" onClick={onSyncSample} disabled={syncing || loading || !readiness?.ready}>
            {syncing ? t("market.syncing") : t("market.syncSample")}
          </Button>
          <Button type="button" variant="outline" onClick={onRefresh} disabled={loading || syncing}>
            {loading ? t("market.refreshing") : t("market.refresh")}
          </Button>
        </CardAction>
      </CardHeader>

      <CardContent className="flex flex-col gap-4">
      {error ? (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      <div className="grid grid-cols-4 gap-3 max-xl:grid-cols-2 max-sm:grid-cols-1">
        <label className="flex flex-col gap-1.5">
          <span className="text-xs font-medium text-muted-foreground">Provider</span>
          <Input
            value={providerFilter}
            placeholder="polygon"
            onChange={(event) => onProviderFilterChange(event.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1.5">
          <span className="text-xs font-medium text-muted-foreground">{t("market.type")}</span>
          <Select value={syncTypeFilter || "all"} onValueChange={(value) => onSyncTypeFilterChange(value === "all" ? "" : value)}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder={t("market.all")} />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectItem value="all">{t("market.all")}</SelectItem>
                <SelectItem value="daily_bars">daily_bars</SelectItem>
                <SelectItem value="bars_1m">bars_1m</SelectItem>
                <SelectItem value="bars_5m">bars_5m</SelectItem>
                <SelectItem value="options_chain">options_chain</SelectItem>
              </SelectGroup>
            </SelectContent>
          </Select>
        </label>
        <label className="flex flex-col gap-1.5">
          <span className="text-xs font-medium text-muted-foreground">{t("market.startedAfter")}</span>
          <Input
            type="datetime-local"
            value={startedAfterFilter}
            onChange={(event) => onStartedAfterFilterChange(event.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1.5">
          <span className="text-xs font-medium text-muted-foreground">{t("market.startedBefore")}</span>
          <Input
            type="datetime-local"
            value={startedBeforeFilter}
            onChange={(event) => onStartedBeforeFilterChange(event.target.value)}
          />
        </label>
      </div>

      {summary ? (
        <div className="grid grid-cols-5 gap-3 max-xl:grid-cols-3 max-md:grid-cols-2 max-sm:grid-cols-1">
          <MetricCard label={t("market.totalRuns")} value={summary.total_runs.toLocaleString()} />
          <MetricCard label={t("market.succeeded")} value={summary.succeeded.toLocaleString()} tone="good" />
          <MetricCard label={t("market.failed")} value={summary.failed.toLocaleString()} tone={summary.failed > 0 ? "bad" : "good"} />
          <MetricCard label={t("market.rowsWritten")} value={summary.rows_written.toLocaleString()} />
          <MetricCard label={t("market.averageDuration")} value={`${summary.average_duration_ms} ms`} />
        </div>
      ) : null}

      {health ? (
        <StatusCard
          label={t("market.schedulerStatus")}
          value={healthStatusLabel(health.status, t)}
          status={health.status}
          detail={[
            health.provider,
            health.sync_type,
            t("market.thresholdMinutes", { minutes: health.stale_after_minutes }),
            health.minutes_since_latest !== null ? t("market.minutesAgo", { minutes: health.minutes_since_latest }) : null,
            health.message,
          ]
            .filter(Boolean)
            .join(" · ")}
        />
      ) : null}

      {readiness ? (
        <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_auto] md:items-center">
          <StatusCard
            label={t("market.providerReadiness")}
            value={readiness.ready ? t("market.ready") : t("market.notReady")}
            status={readiness.ready ? "ready" : "not-ready"}
            detail={`${readiness.provider} · ${
              readiness.missing.length > 0 ? t("market.missing", { items: readiness.missing.join(", ") }) : t("market.runtimeReady")
            } · ${readiness.message}`}
          />
          {!readiness.ready ? (
            <Button type="button" onClick={onConfigureProvider}>
              {t("market.configureProvider")}
            </Button>
          ) : null}
        </div>
      ) : null}

      {groups.length > 0 ? (
        <div className="grid grid-cols-2 gap-3 max-lg:grid-cols-1">
          {groups.map((group) => (
            <article key={`${group.provider}:${group.sync_type}`} className="rounded-xl border bg-card p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="min-w-0">
                  <strong className="block truncate text-sm">{group.provider}</strong>
                  <span className="text-xs text-muted-foreground">{group.sync_type}</span>
                </div>
                <Badge variant={group.failed > 0 ? "destructive" : "secondary"}>
                  {group.succeeded}/{group.total_runs}
                </Badge>
              </div>
              <div className="mt-3 flex flex-wrap gap-3 text-xs text-muted-foreground">
                <span>{group.failed} {t("market.failed")}</span>
                <span>{group.rows_written.toLocaleString()} rows</span>
                <span>{group.average_duration_ms} ms</span>
              </div>
            </article>
          ))}
        </div>
      ) : null}

      {runs.length === 0 && !error ? (
        <p className="text-sm text-muted-foreground">{t("market.noSyncRuns")}</p>
      ) : (
        <div className="grid gap-2">
          {runs.map((run) => (
            <article key={run.id} className="rounded-xl border bg-card p-3">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={run.status === "succeeded" ? "secondary" : "destructive"}>{run.status}</Badge>
                <strong>{run.provider}</strong>
              </div>
              <div className="mt-2 flex flex-wrap gap-3 text-xs text-muted-foreground">
                <span>{run.sync_type}</span>
                <span>{run.rows_written.toLocaleString()} rows</span>
                <span>{formatDate(run.finished_at ?? run.started_at)}</span>
              </div>
              {run.error_message ? <p className="mt-2 text-sm text-destructive">{run.error_message}</p> : null}
            </article>
          ))}
        </div>
      )}
      </CardContent>
    </Card>
  );
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function healthStatusLabel(status: string, t: (key: string) => string) {
  if (["ok", "stale", "failing", "missing"].includes(status)) {
    return t(`market.health.${status}`);
  }
  return status;
}
