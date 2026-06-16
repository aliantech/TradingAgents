import type { AnalysisStatus } from "../../lib/api";

type AnalysisPanelProps = {
  symbol: string;
  loading: boolean;
  error: string | null;
  status: AnalysisStatus | null;
  onSymbolChange: (symbol: string) => void;
  onRunAnalysis: () => void;
};

export function AnalysisPanel({ symbol, loading, error, status, onSymbolChange, onRunAnalysis }: AnalysisPanelProps) {
  return (
    <section className="panel analysis-panel">
      <div className="panel-header">
        <div>
          <h2>AI 分析</h2>
          <p>输入美股、ETF 或指数标的，生成中文结构化投研报告。</p>
        </div>
        <button type="button" onClick={onRunAnalysis} disabled={loading}>
          {loading ? "分析中" : "开始分析"}
        </button>
      </div>

      <label className="field">
        <span>标的</span>
        <input value={symbol} onChange={(event) => onSymbolChange(event.target.value.toUpperCase())} />
      </label>

      {error ? <div className="alert">{error}</div> : null}

      <div className="progress-list">
        {(status?.progress ?? []).map((event) => (
          <div className="progress-item" key={event.step}>
            <span className="dot" />
            <div>
              <strong>{event.step}</strong>
              <p>{event.message}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
