import type { ResearchReport } from "../../lib/api";
import type React from "react";
import { useTranslation } from "react-i18next";
import { Download, FileJson, Layers3, ShieldAlert, Target, Workflow } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { CardAction } from "@/components/ui/card";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

type ReportPanelProps = {
  report: ResearchReport | null;
};

export function ReportPanel({ report }: ReportPanelProps) {
  const { t } = useTranslation();
  if (!report) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{t("reports.emptyTitle")}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 rounded-lg border border-dashed p-4">
            <div className="flex items-center gap-2">
              <Workflow className="text-muted-foreground" />
              <p className="text-sm font-semibold">{t("reports.emptyWorkflow")}</p>
            </div>
            <p className="text-sm leading-6 text-muted-foreground">{t("reports.empty")}</p>
          </div>
        </CardContent>
      </Card>
    );
  }
  const sections = reportSections(report, t);
  const populatedSections = sections.filter((section) => section.body.trim()).length;

  return (
    <Card>
      <CardHeader>
        <div className="flex min-w-0 flex-col gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">{t("reports.outputWorkbench")}</Badge>
            <Badge variant="outline">{report.language.toUpperCase()}</Badge>
            <Badge variant="outline">{report.analyst_set}</Badge>
          </div>
          <CardTitle>{t("reports.reportTitle", { symbol: report.symbol })}</CardTitle>
        </div>
        <CardAction className="flex gap-2">
          <Button type="button" variant="outline" size="sm" onClick={() => downloadText(reportMarkdown(report), `${report.symbol}-report.md`)}>
            <Download data-icon="inline-start" />
            {t("reports.downloadMarkdown")}
          </Button>
          <Button type="button" variant="outline" size="sm" onClick={() => downloadText(reportJson(report), `${report.symbol}-report.json`)}>
            <FileJson data-icon="inline-start" />
            {t("reports.downloadJson")}
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <Alert>
          <AlertDescription>
            {t("reports.riskNotice")}
          </AlertDescription>
        </Alert>

        <div className="grid grid-cols-4 gap-3 max-lg:grid-cols-2 max-sm:grid-cols-1">
          <ReportFact icon={<Target />} label={t("reports.factSymbol")} value={report.symbol} />
          <ReportFact icon={<Layers3 />} label={t("reports.factSections")} value={`${populatedSections}/${sections.length}`} />
          <ReportFact icon={<Workflow />} label={t("reports.factAnalystSet")} value={report.analyst_set} />
          <ReportFact icon={<ShieldAlert />} label={t("reports.factRiskTags")} value={report.risk_factors.length.toLocaleString()} />
        </div>

        <div className="grid grid-cols-3 gap-3 max-xl:grid-cols-2 max-sm:grid-cols-1">
          {sections.slice(0, 6).map((section) => (
            <div key={section.key} className="rounded-lg border bg-background p-3">
              <div className="flex items-center justify-between gap-2">
                <p className="text-xs font-medium text-muted-foreground">{section.title}</p>
                <Badge variant={section.body.trim() ? "secondary" : "outline"}>
                  {section.body.trim() ? t("reports.sectionReady") : t("reports.sectionEmpty")}
                </Badge>
              </div>
              <p className="mt-2 line-clamp-2 text-sm leading-6 text-muted-foreground">{section.body || t("reports.sectionEmptyDetail")}</p>
            </div>
          ))}
        </div>

        <Tabs defaultValue="structured">
          <TabsList className="flex-wrap">
            <TabsTrigger value="structured">{t("reports.structured")}</TabsTrigger>
            <TabsTrigger value="markdown">Markdown</TabsTrigger>
            <TabsTrigger value="json">JSON</TabsTrigger>
          </TabsList>

          <TabsContent value="structured">
            <Tabs defaultValue="summary" className="mt-2">
              <TabsList variant="line" className="flex-wrap">
                {sections.map((section) => (
                  <TabsTrigger key={section.key} value={section.key}>
                    {section.title}
                  </TabsTrigger>
                ))}
              </TabsList>
              {sections.map((section) => (
                <TabsContent key={section.key} value={section.key} className="pt-3">
                  <ReportSection title={section.title} body={section.body} />
                </TabsContent>
              ))}
            </Tabs>
          </TabsContent>

          <TabsContent value="markdown">
            <MarkdownView markdown={reportMarkdown(report)} />
          </TabsContent>

          <TabsContent value="json">
            <pre className="max-h-[520px] overflow-auto rounded-lg border bg-muted/40 p-3 text-xs leading-5">
              {reportJson(report)}
            </pre>
          </TabsContent>
        </Tabs>

        <Separator />
        <div className="rounded-lg border bg-background p-3">
          <div className="mb-3 flex items-center gap-2">
            <ShieldAlert className="text-muted-foreground" />
            <h3 className="text-sm font-semibold">{t("reports.riskTags")}</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {report.risk_factors.length ? report.risk_factors.map((risk) => (
              <Badge key={risk} variant="outline">{risk}</Badge>
            )) : <span className="text-sm text-muted-foreground">{t("reports.noRiskTags")}</span>}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function ReportFact({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-lg border bg-background p-3">
      <div className="mb-2 flex items-center gap-2 text-muted-foreground">{icon}</div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 truncate text-sm font-semibold">{value}</p>
    </div>
  );
}

function reportSections(report: ResearchReport, t: (key: string) => string) {
  return [
    { key: "summary", title: t("reports.sections.summary"), body: report.summary },
    { key: "background", title: t("reports.sections.background"), body: report.market_background },
    { key: "fundamental", title: t("reports.sections.fundamental"), body: report.fundamental_analysis },
    { key: "technical", title: t("reports.sections.technical"), body: report.technical_analysis },
    { key: "sentiment", title: t("reports.sections.sentiment"), body: report.sentiment_analysis },
    { key: "options", title: t("reports.sections.options"), body: report.options_observation },
    { key: "bull", title: t("reports.sections.bull"), body: report.bull_case },
    { key: "bear", title: t("reports.sections.bear"), body: report.bear_case },
    { key: "plan", title: t("reports.sections.plan"), body: report.trade_plan },
    { key: "sizing", title: t("reports.sections.sizing"), body: report.position_sizing },
    { key: "risk", title: t("reports.sections.risk"), body: report.take_profit_stop_loss },
  ];
}

function ReportSection({ title, body }: { title: string; body: string }) {
  return (
    <section>
      <h3 className="mb-2 text-base font-semibold">{title}</h3>
      <p className="text-sm leading-6 text-muted-foreground">{body}</p>
    </section>
  );
}

function MarkdownView({ markdown }: { markdown: string }) {
  return (
    <article className="max-h-[520px] overflow-auto rounded-lg border bg-background p-4">
      {markdown.split(/\n{2,}/).map((block, index) => (
        <MarkdownBlock key={`${index}-${block.slice(0, 12)}`} block={block} />
      ))}
    </article>
  );
}

function MarkdownBlock({ block }: { block: string }) {
  const trimmed = block.trim();
  if (!trimmed) return null;
  if (trimmed.startsWith("### ")) return <h3 className="mb-2 mt-4 text-base font-semibold">{trimmed.slice(4)}</h3>;
  if (trimmed.startsWith("## ")) return <h2 className="mb-2 mt-5 text-lg font-semibold">{trimmed.slice(3)}</h2>;
  if (trimmed.startsWith("# ")) return <h1 className="mb-3 text-xl font-semibold">{trimmed.slice(2)}</h1>;
  if (trimmed.split("\n").every((line) => line.trim().startsWith("- "))) {
    return (
      <ul className="mb-3 list-disc pl-5 text-sm leading-6 text-muted-foreground">
        {trimmed.split("\n").map((line) => (
          <li key={line}>{line.trim().slice(2)}</li>
        ))}
      </ul>
    );
  }
  return <p className="mb-3 text-sm leading-6 text-muted-foreground whitespace-pre-wrap">{trimmed}</p>;
}

function reportMarkdown(report: ResearchReport) {
  if (report.markdown?.trim()) return report.markdown;
  const sections = reportMarkdownSections(report).map((section) => `## ${section.title}\n\n${section.body}`).join("\n\n");
  const risks = report.risk_factors.length ? `\n\n## 风险标签\n\n${report.risk_factors.map((risk) => `- ${risk}`).join("\n")}` : "";
  return `# ${report.symbol} 中文报告\n\n${sections}${risks}`;
}

function reportMarkdownSections(report: ResearchReport) {
  return [
    { title: "摘要", body: report.summary },
    { title: "市场背景", body: report.market_background },
    { title: "基本面", body: report.fundamental_analysis },
    { title: "技术面", body: report.technical_analysis },
    { title: "情绪面", body: report.sentiment_analysis },
    { title: "期权观察", body: report.options_observation },
    { title: "多头观点", body: report.bull_case },
    { title: "空头观点", body: report.bear_case },
    { title: "交易计划", body: report.trade_plan },
    { title: "仓位参考", body: report.position_sizing },
    { title: "风控参考", body: report.take_profit_stop_loss },
  ];
}

function reportJson(report: ResearchReport) {
  return JSON.stringify(report, null, 2);
}

function downloadText(content: string, filename: string) {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
