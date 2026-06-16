import type {
  ProviderReadiness,
  ProviderSyncHealth,
  ProviderSyncRunItem,
  ProviderSyncSummary,
  ProviderSyncSummaryGroup,
} from "../../lib/api";

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
  onRefresh,
  onSyncSample,
}: DataSyncPanelProps) {
  return (
    <section className="panel sync-panel">
      <div className="panel-header">
        <div>
          <h3>数据源同步</h3>
          <p>行情写入和 provider 审计记录。</p>
        </div>
        <div className="sync-actions">
          <button type="button" className="secondary-button" onClick={onSyncSample} disabled={syncing || loading}>
            {syncing ? "同步中" : "同步 SPY"}
          </button>
          <button type="button" className="secondary-button" onClick={onRefresh} disabled={loading || syncing}>
            {loading ? "刷新中" : "刷新"}
          </button>
        </div>
      </div>

      {error ? <div className="alert">{error}</div> : null}

      <div className="sync-filters">
        <label>
          <span>Provider</span>
          <input
            value={providerFilter}
            placeholder="sample / polygon"
            onChange={(event) => onProviderFilterChange(event.target.value)}
          />
        </label>
        <label>
          <span>类型</span>
          <select value={syncTypeFilter} onChange={(event) => onSyncTypeFilterChange(event.target.value)}>
            <option value="">全部</option>
            <option value="daily_bars">daily_bars</option>
            <option value="bars_1m">bars_1m</option>
            <option value="bars_5m">bars_5m</option>
          </select>
        </label>
        <label>
          <span>开始</span>
          <input
            type="datetime-local"
            value={startedAfterFilter}
            onChange={(event) => onStartedAfterFilterChange(event.target.value)}
          />
        </label>
        <label>
          <span>结束</span>
          <input
            type="datetime-local"
            value={startedBeforeFilter}
            onChange={(event) => onStartedBeforeFilterChange(event.target.value)}
          />
        </label>
      </div>

      {summary ? (
        <div className="sync-summary">
          <Metric label="总次数" value={summary.total_runs.toLocaleString()} />
          <Metric label="成功" value={summary.succeeded.toLocaleString()} />
          <Metric label="失败" value={summary.failed.toLocaleString()} />
          <Metric label="写入" value={summary.rows_written.toLocaleString()} />
          <Metric label="平均耗时" value={`${summary.average_duration_ms} ms`} />
        </div>
      ) : null}

      {health ? (
        <div className={`sync-health ${health.status}`}>
          <div>
            <span>调度状态</span>
            <strong>{healthStatusLabel(health.status)}</strong>
          </div>
          <div>
            <span>{health.provider}</span>
            <span>{health.sync_type}</span>
            <span>阈值 {health.stale_after_minutes} 分钟</span>
            {health.minutes_since_latest !== null ? <span>{health.minutes_since_latest} 分钟前</span> : null}
          </div>
          <p>{health.message}</p>
        </div>
      ) : null}

      {readiness ? (
        <div className={`provider-readiness ${readiness.ready ? "ready" : "not-ready"}`}>
          <div>
            <span>Provider 准备状态</span>
            <strong>{readiness.ready ? "可用" : "未就绪"}</strong>
          </div>
          <div>
            <span>{readiness.provider}</span>
            {readiness.missing.length > 0 ? <span>缺少 {readiness.missing.join(", ")}</span> : <span>运行时配置已就绪</span>}
          </div>
          <p>{readiness.message}</p>
        </div>
      ) : null}

      {groups.length > 0 ? (
        <div className="sync-groups">
          {groups.map((group) => (
            <article key={`${group.provider}:${group.sync_type}`} className="sync-group">
              <div>
                <strong>{group.provider}</strong>
                <span>{group.sync_type}</span>
              </div>
              <div>
                <span>{group.succeeded}/{group.total_runs} 成功</span>
                <span>{group.failed} 失败</span>
                <span>{group.rows_written.toLocaleString()} rows</span>
                <span>{group.average_duration_ms} ms</span>
              </div>
            </article>
          ))}
        </div>
      ) : null}

      {runs.length === 0 && !error ? (
        <p className="empty">暂无同步记录</p>
      ) : (
        <div className="sync-list">
          {runs.map((run) => (
            <article key={run.id} className="sync-item">
              <div>
                <span className={`sync-status ${run.status}`}>{run.status}</span>
                <strong>{run.provider}</strong>
              </div>
              <div className="sync-meta">
                <span>{run.sync_type}</span>
                <span>{run.rows_written.toLocaleString()} rows</span>
                <span>{formatDate(run.finished_at ?? run.started_at)}</span>
              </div>
              {run.error_message ? <p className="sync-error">{run.error_message}</p> : null}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="sync-metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
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

function healthStatusLabel(status: string) {
  const labels: Record<string, string> = {
    ok: "正常",
    stale: "过期",
    failing: "失败告警",
    missing: "无记录",
  };
  return labels[status] ?? status;
}
