import type { ResearchReport } from "../../lib/api";

type ReportPanelProps = {
  report: ResearchReport | null;
};

export function ReportPanel({ report }: ReportPanelProps) {
  if (!report) {
    return (
      <section className="panel report-panel">
        <h2>中文报告</h2>
        <p className="empty">启动一次分析后，这里会显示中文结构化报告。</p>
      </section>
    );
  }

  return (
    <section className="panel report-panel">
      <div className="panel-header">
        <div>
          <h2>{report.symbol} 中文报告</h2>
          <p>置信度 {(report.confidence * 100).toFixed(0)}%</p>
        </div>
      </div>
      <article className="report-grid">
        <ReportSection title="摘要" body={report.summary} />
        <ReportSection title="市场背景" body={report.market_background} />
        <ReportSection title="技术面" body={report.technical_analysis} />
        <ReportSection title="期权市场观察" body={report.options_observation} />
        <ReportSection title="多头观点" body={report.bull_case} />
        <ReportSection title="空头观点" body={report.bear_case} />
        <ReportSection title="交易计划" body={report.trade_plan} />
        <ReportSection title="风控参考" body={report.take_profit_stop_loss} />
      </article>
      <div className="risk-tags">
        {report.risk_factors.map((risk) => (
          <span key={risk}>{risk}</span>
        ))}
      </div>
    </section>
  );
}

function ReportSection({ title, body }: { title: string; body: string }) {
  return (
    <section>
      <h3>{title}</h3>
      <p>{body}</p>
    </section>
  );
}
