import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type MetricTone = "good" | "warn" | "bad";

const toneClasses: Record<MetricTone, string> = {
  good: "bg-primary",
  warn: "bg-muted-foreground",
  bad: "bg-destructive",
};

export function MetricCard({
  label,
  value,
  helper,
  tone,
  className,
}: {
  label: string;
  value: string;
  helper?: string;
  tone?: MetricTone;
  className?: string;
}) {
  return (
    <Card size="sm" className={cn("min-h-[76px]", className)}>
      <CardContent className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-xs font-medium text-muted-foreground">{label}</p>
          <p className="mt-1 truncate text-xl font-semibold tabular-nums tracking-normal">{value}</p>
          {helper ? <p className="mt-1 truncate text-xs text-muted-foreground">{helper}</p> : null}
        </div>
        {tone ? <span aria-hidden="true" className={cn("mt-1 size-2.5 shrink-0 rounded-full", toneClasses[tone])} /> : null}
      </CardContent>
    </Card>
  );
}

export function StatusCard({
  label,
  value,
  status,
  detail,
  className,
}: {
  label: string;
  value: string;
  status: string;
  detail: string;
  className?: string;
}) {
  const isGood = ["ready", "ok", "succeeded", "completed"].includes(status);
  const isBad = ["failing", "failed", "error"].includes(status);

  return (
    <Card size="sm" className={className}>
      <CardContent>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <p className="text-xs font-medium text-muted-foreground">{label}</p>
          <Badge variant={isGood ? "secondary" : isBad ? "destructive" : "outline"}>{value}</Badge>
        </div>
        <p className="mt-2 text-sm leading-6 text-muted-foreground">{detail}</p>
      </CardContent>
    </Card>
  );
}
