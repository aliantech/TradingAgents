import type { ProviderSyncRunItem } from "../../lib/api";

type DataSyncPanelProps = {
  runs: ProviderSyncRunItem[];
  loading: boolean;
  syncing: boolean;
  error: string | null;
  onRefresh: () => void;
  onSyncSample: () => void;
};

export function DataSyncPanel({ runs, loading, syncing, error, onRefresh, onSyncSample }: DataSyncPanelProps) {
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

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}
