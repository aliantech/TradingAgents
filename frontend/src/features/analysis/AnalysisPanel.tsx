import type { AnalysisStartPayload, AnalysisStatus } from "../../lib/api";
import type React from "react";
import { useTranslation } from "react-i18next";
import { Bot, CalendarDays, CheckCircle2, CircleDashed, Layers3, Play, ShieldCheck, Workflow } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardAction, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";

type AnalysisConfig = Pick<
  AnalysisStartPayload,
  "analysisDate" | "llmProvider" | "model" | "depth" | "analystSet" | "researchTemplate"
>;

type AnalysisPanelProps = {
  symbol: string;
  supportedSymbols: string[];
  config: AnalysisConfig;
  loading: boolean;
  error: string | null;
  status: AnalysisStatus | null;
  onSymbolChange: (symbol: string) => void;
  onConfigChange: (config: AnalysisConfig) => void;
  onRunAnalysis: () => void;
};

const MODEL_OPTIONS: Record<string, string[]> = {
  openai: ["gpt-5.5", "gpt-5", "gpt-4.1"],
  anthropic: ["claude-sonnet-4", "claude-opus-4"],
  google: ["gemini-2.5-pro", "gemini-2.5-flash"],
};

export function AnalysisPanel({
  symbol,
  supportedSymbols,
  config,
  loading,
  error,
  status,
  onSymbolChange,
  onConfigChange,
  onRunAnalysis,
}: AnalysisPanelProps) {
  const { t } = useTranslation();
  const modelOptions = MODEL_OPTIONS[config.llmProvider] ?? MODEL_OPTIONS.openai;
  const updateConfig = (next: Partial<AnalysisConfig>) => onConfigChange({ ...config, ...next });
  const normalizedSymbol = symbol.trim().toUpperCase();
  const supportedMarket = supportedSymbols.includes(normalizedSymbol);
  const teamAgents = agentLabels(config.analystSet, t);
  const runStatus = status?.status ?? "idle";

  return (
    <Card>
      <CardHeader>
        <div className="flex min-w-0 flex-col gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">{t("analysis.launchpad")}</Badge>
            <Badge variant={supportedMarket ? "default" : "destructive"}>{supportedMarket ? t("analysis.inScope") : t("analysis.outOfScope")}</Badge>
            <Badge variant="outline">{runStatus}</Badge>
          </div>
          <CardTitle>{t("analysis.title")}</CardTitle>
        </div>
        <CardAction>
          <Button type="button" onClick={onRunAnalysis} disabled={loading || !supportedMarket}>
            <Play data-icon="inline-start" />
            {loading ? t("analysis.running") : t("analysis.start")}
          </Button>
        </CardAction>
      </CardHeader>

      <CardContent className="flex flex-col gap-4">
        <div className="grid grid-cols-[minmax(0,1.05fr)_minmax(300px,0.95fr)] gap-4 max-xl:grid-cols-1">
          <div className="grid gap-3">
            <section className="rounded-lg border bg-background p-3">
              <div className="mb-3 flex items-center gap-2">
                <Layers3 className="text-muted-foreground" />
                <h3 className="text-sm font-semibold">{t("analysis.contractTitle")}</h3>
              </div>
              <div className="grid grid-cols-2 gap-3 max-sm:grid-cols-1">
                <label className="flex flex-col gap-2">
                  <span className="text-xs font-medium text-muted-foreground">{t("analysis.symbol")}</span>
                  <Input value={symbol} onChange={(event) => onSymbolChange(event.target.value.toUpperCase())} />
                  {!supportedMarket ? (
                    <span className="text-xs text-destructive">
                      {t("analysis.unsupported", {
                        symbol: normalizedSymbol || t("analysis.emptySymbol"),
                        symbols: supportedSymbols.join(", "),
                      })}
                    </span>
                  ) : null}
                </label>
                <label className="flex flex-col gap-2">
                  <span className="text-xs font-medium text-muted-foreground">{t("analysis.date")}</span>
                  <Input
                    type="date"
                    value={config.analysisDate}
                    onChange={(event) => updateConfig({ analysisDate: event.target.value })}
                  />
                </label>
              </div>
            </section>

            <section className="rounded-lg border bg-background p-3">
              <div className="mb-3 flex items-center gap-2">
                <Bot className="text-muted-foreground" />
                <h3 className="text-sm font-semibold">{t("analysis.modelStack")}</h3>
              </div>
              <div className="grid grid-cols-2 gap-3 max-sm:grid-cols-1">
                <label className="flex flex-col gap-2">
                  <span className="text-xs font-medium text-muted-foreground">{t("analysis.provider")}</span>
                  <Select
                    value={config.llmProvider}
                    onValueChange={(llmProvider) =>
                      updateConfig({ llmProvider, model: MODEL_OPTIONS[llmProvider]?.[0] ?? config.model })
                    }
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectGroup>
                        <SelectItem value="openai">OpenAI</SelectItem>
                        <SelectItem value="anthropic">Anthropic</SelectItem>
                        <SelectItem value="google">Google</SelectItem>
                      </SelectGroup>
                    </SelectContent>
                  </Select>
                </label>
                <label className="flex flex-col gap-2">
                  <span className="text-xs font-medium text-muted-foreground">{t("analysis.model")}</span>
                  <Select value={config.model} onValueChange={(model) => updateConfig({ model })}>
                    <SelectTrigger className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectGroup>
                        {modelOptions.map((model) => (
                          <SelectItem key={model} value={model}>
                            {model}
                          </SelectItem>
                        ))}
                      </SelectGroup>
                    </SelectContent>
                  </Select>
                </label>
              </div>
            </section>
          </div>

          <section className="rounded-lg border bg-background p-3">
            <div className="mb-3 flex items-center gap-2">
              <Workflow className="text-muted-foreground" />
              <h3 className="text-sm font-semibold">{t("analysis.workflowTitle")}</h3>
            </div>
            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-2">
                <span className="text-xs font-medium text-muted-foreground">{t("analysis.template")}</span>
                <Select
                  value={config.researchTemplate}
                  onValueChange={(researchTemplate) => {
                    if (
                      researchTemplate === "general" ||
                      researchTemplate === "earnings-preview" ||
                      researchTemplate === "macro-options-readthrough" ||
                      researchTemplate === "technical-setup"
                    ) {
                      updateConfig({ researchTemplate });
                    }
                  }}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectGroup>
                      <SelectItem value="general">{t("analysis.templates.general")}</SelectItem>
                      <SelectItem value="earnings-preview">{t("analysis.templates.earnings-preview")}</SelectItem>
                      <SelectItem value="macro-options-readthrough">{t("analysis.templates.macro-options-readthrough")}</SelectItem>
                      <SelectItem value="technical-setup">{t("analysis.templates.technical-setup")}</SelectItem>
                    </SelectGroup>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex flex-col gap-2">
                <span className="text-xs font-medium text-muted-foreground">{t("analysis.depth")}</span>
                <ToggleGroup
                  type="single"
                  value={config.depth}
                  onValueChange={(depth) => {
                    if (depth === "quick" || depth === "standard" || depth === "deep") {
                      updateConfig({ depth });
                    }
                  }}
                  className="justify-start"
                >
                  <ToggleGroupItem value="quick">{t("analysis.depthQuick")}</ToggleGroupItem>
                  <ToggleGroupItem value="standard">{t("analysis.depthStandard")}</ToggleGroupItem>
                  <ToggleGroupItem value="deep">{t("analysis.depthDeep")}</ToggleGroupItem>
                </ToggleGroup>
              </div>

              <div className="flex flex-col gap-2">
                <span className="text-xs font-medium text-muted-foreground">{t("analysis.team")}</span>
                <ToggleGroup
                  type="single"
                  value={config.analystSet}
                  onValueChange={(analystSet) => {
                    if (analystSet) {
                      updateConfig({ analystSet });
                    }
                  }}
                  className="justify-start"
                >
                  <ToggleGroupItem value="core">{t("analysis.teamCore")}</ToggleGroupItem>
                  <ToggleGroupItem value="macro-options">{t("analysis.teamMacroOptions")}</ToggleGroupItem>
                  <ToggleGroupItem value="full">{t("analysis.teamFull")}</ToggleGroupItem>
                </ToggleGroup>
              </div>

              <div className="grid gap-2">
                {teamAgents.map((agent) => (
                  <div key={agent} className="flex items-center justify-between gap-3 rounded-lg border bg-muted/30 px-3 py-2">
                    <span className="text-sm font-medium">{agent}</span>
                    <Badge variant="outline">{t("analysis.agentReady")}</Badge>
                  </div>
                ))}
              </div>
            </div>
          </section>
        </div>

        <div className="grid grid-cols-4 gap-3 max-lg:grid-cols-2 max-sm:grid-cols-1">
          <AnalysisFact icon={<CalendarDays />} label={t("analysis.runDate")} value={config.analysisDate} />
          <AnalysisFact icon={<Bot />} label={t("analysis.runModel")} value={`${config.llmProvider} · ${config.model}`} />
          <AnalysisFact icon={<ShieldCheck />} label={t("analysis.template")} value={t(`analysis.templates.${config.researchTemplate}`)} />
          <AnalysisFact icon={<Workflow />} label={t("analysis.runTeam")} value={teamAgents.join(" / ")} />
        </div>

        {error ? (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}

        <div className="rounded-lg border bg-background p-3">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 className="text-sm font-semibold">{t("analysis.progressTitle")}</h3>
            </div>
            <Badge variant={loading ? "default" : "outline"}>{loading ? t("analysis.running") : runStatus}</Badge>
          </div>
          <div className="flex flex-col gap-3">
            {(status?.progress?.length ? status.progress : defaultProgress(t)).map((event) => (
              <div className="grid grid-cols-[20px_1fr] gap-3 rounded-lg border p-3" key={event.step}>
                {event.status === "completed" ? <CheckCircle2 className="mt-0.5 text-primary" /> : <CircleDashed className="mt-0.5 text-muted-foreground" />}
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <strong className="text-sm">{event.step}</strong>
                    <Badge variant={event.status === "completed" ? "default" : "secondary"}>{event.status}</Badge>
                  </div>
                  {event.message ? <p className="mt-1 text-sm leading-6 text-muted-foreground">{event.message}</p> : null}
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function AnalysisFact({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-lg border bg-background p-3">
      <div className="mb-2 flex items-center gap-2 text-muted-foreground">{icon}</div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 truncate text-sm font-semibold">{value}</p>
    </div>
  );
}

function agentLabels(analystSet: string, t: (key: string) => string) {
  if (analystSet === "full") {
    return [
      t("analysis.agentMarket"),
      t("analysis.agentFundamental"),
      t("analysis.agentTechnical"),
      t("analysis.agentSentiment"),
      t("analysis.agentOptions"),
      t("analysis.agentRisk"),
    ];
  }
  if (analystSet === "macro-options") {
    return [t("analysis.agentMarket"), t("analysis.agentTechnical"), t("analysis.agentOptions"), t("analysis.agentRisk")];
  }
  return [t("analysis.agentMarket"), t("analysis.agentTechnical"), t("analysis.agentRisk")];
}

function defaultProgress(t: (key: string) => string): AnalysisStatus["progress"] {
  return [
    { step: t("analysis.progressData"), status: t("analysis.pending"), message: "" },
    { step: t("analysis.progressAgents"), status: t("analysis.pending"), message: "" },
    { step: t("analysis.progressReport"), status: t("analysis.pending"), message: "" },
  ];
}
