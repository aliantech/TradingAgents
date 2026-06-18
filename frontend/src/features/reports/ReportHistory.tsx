import type { AnalysisRunItem, ReportListItem } from "../../lib/api";
import { useTranslation } from "react-i18next";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type ReportHistoryProps = {
  reports: ReportListItem[];
  runs: AnalysisRunItem[];
  onSelectReport: (reportId: string) => void;
};

export function ReportHistory({ reports, runs, onSelectReport }: ReportHistoryProps) {
  const { t } = useTranslation();
  const runsById = new Map(runs.map((run) => [run.analysis_id, run]));
  const completedReports = reports.filter((report) => runsById.get(report.analysis_id)?.status === "completed" || !runsById.get(report.analysis_id)).length;
  const averageConfidence = reports.length
    ? Math.round(reports.reduce((total, report) => total + report.confidence, 0) * 100 / reports.length)
    : 0;
  const analystSets = new Set(reports.map((report) => runsById.get(report.analysis_id)?.analyst_set ?? report.analyst_set));

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("reports.historyTitle")}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
      <div className="grid grid-cols-3 gap-3 max-sm:grid-cols-1">
        <ReportHistoryMetric label={t("reports.historyCount")} value={reports.length.toLocaleString()} />
        <ReportHistoryMetric label={t("reports.historyCompleted")} value={completedReports.toLocaleString()} />
        <ReportHistoryMetric label={t("reports.historyConfidence")} value={`${averageConfidence}%`} />
      </div>
      <div className="flex flex-wrap gap-2">
        {[...analystSets].map((set) => (
          <Badge key={set} variant="outline">{set}</Badge>
        ))}
      </div>
      {reports.length ? (
        <div className="flex flex-col gap-2">
          {reports.map((report) => {
            const run = runsById.get(report.analysis_id);
            return (
              <Button
                key={report.report_id}
                type="button"
                variant="outline"
                className="h-auto justify-start px-3 py-3 text-left"
                onClick={() => onSelectReport(report.report_id)}
              >
                <span className="flex min-w-0 flex-1 flex-col gap-2">
                  <span className="flex flex-wrap items-center gap-2">
                    <strong>{t("reports.reportTitle", { symbol: report.symbol })}</strong>
                    <Badge variant="secondary">{run?.status ?? "report"}</Badge>
                    <Badge variant="secondary">{run?.analyst_set ?? report.analyst_set}</Badge>
                    <Badge variant="secondary">{t("reports.confidence")} {(report.confidence * 100).toFixed(0)}%</Badge>
                  </span>
                  <span className="line-clamp-2 text-xs text-muted-foreground">{report.summary}</span>
                  <span className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                    <span>Run {report.analysis_id.slice(0, 8)}</span>
                    <span>{run ? `${run.llm_provider} · ${run.model}` : "model pending"}</span>
                    <span>{run?.depth ?? "depth pending"}</span>
                    <span>{run?.analyst_set ?? report.analyst_set}</span>
                    <span>{run ? formatDate(run.created_at) : "created time pending"}</span>
                  </span>
                </span>
              </Button>
            );
          })}
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">{t("reports.noReports")}</p>
      )}
      </CardContent>
    </Card>
  );
}

function ReportHistoryMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border bg-background p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-lg font-semibold">{value}</p>
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
