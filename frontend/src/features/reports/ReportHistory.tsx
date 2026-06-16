import type { ReportListItem } from "../../lib/api";

type ReportHistoryProps = {
  reports: ReportListItem[];
  onSelectReport: (reportId: string) => void;
};

export function ReportHistory({ reports, onSelectReport }: ReportHistoryProps) {
  return (
    <section className="panel history-panel">
      <h2>报告历史</h2>
      {reports.length ? (
        <div className="history-list">
          {reports.map((report) => (
            <button key={report.report_id} type="button" onClick={() => onSelectReport(report.report_id)}>
              <strong>{report.symbol}</strong>
              <span>{report.summary}</span>
            </button>
          ))}
        </div>
      ) : (
        <p className="empty">暂无报告。</p>
      )}
    </section>
  );
}
