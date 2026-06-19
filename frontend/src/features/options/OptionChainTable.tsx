import { Fragment, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
} from "@tanstack/react-table";

import type { MarketTimeframe, OptionBar, OptionContract, OptionSnapshot, ProviderReadiness, ProviderSyncHealth, ProviderSyncRunItem } from "../../lib/api";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardAction, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { cn } from "@/lib/utils";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  filterRowsByMoneyness,
  formatOptionNumber,
  formatOptionPercent,
  groupOptionSnapshots,
  type MoneynessFilter,
  type OptionChainRow,
} from "./optionChain";

type OptionChainTableProps = {
  snapshots: OptionSnapshot[];
  contracts: OptionContract[];
  contractsLoading: boolean;
  contractsError: string | null;
  underlying: string;
  expiry: string;
  loading: boolean;
  syncing: boolean;
  error: string | null;
  readiness: ProviderReadiness | null;
  syncHealth: ProviderSyncHealth | null;
  latestSyncRun: ProviderSyncRunItem | null;
  selectedBars: OptionBar[];
  selectedBarsLoading: boolean;
  selectedBarsError: string | null;
  selectedBarsTimeframe: MarketTimeframe;
  onExpiryChange: (value: string) => void;
  onSelectedContractChange: (optionSymbol: string) => void;
  onSelectedBarsTimeframeChange: (timeframe: MarketTimeframe) => void;
  onConfigureProvider: () => void;
  onRefresh: () => void;
  onSync: () => void;
};

type SelectedQuoteField = "last" | "bid" | "ask";
type ColumnPreset = "essential" | "greeks" | "liquidity";
type OptionColumn = "delta" | "iv" | "oi" | "vol" | "last" | "bid" | "ask";

const MARKET_COLORS = {
  up: "#16a34a",
  down: "#dc2626",
};

const COLUMN_LABELS: Record<OptionColumn, string> = {
  delta: "Delta",
  iv: "IV",
  oi: "OI",
  vol: "Vol",
  last: "Last",
  bid: "Bid",
  ask: "Ask",
};

const COLUMN_PRESETS: Record<ColumnPreset, { call: OptionColumn[]; put: OptionColumn[] }> = {
  essential: {
    call: ["last", "bid", "ask"],
    put: ["bid", "ask", "last"],
  },
  greeks: {
    call: ["delta", "iv", "last", "bid", "ask"],
    put: ["bid", "ask", "last", "iv", "delta"],
  },
  liquidity: {
    call: ["oi", "vol", "last", "bid", "ask"],
    put: ["bid", "ask", "last", "vol", "oi"],
  },
};

export function OptionChainTable({
  snapshots,
  contracts,
  contractsLoading,
  contractsError,
  underlying,
  expiry,
  loading,
  syncing,
  error,
  readiness,
  syncHealth,
  latestSyncRun,
  selectedBars,
  selectedBarsLoading,
  selectedBarsError,
  selectedBarsTimeframe,
  onExpiryChange,
  onSelectedContractChange,
  onSelectedBarsTimeframeChange,
  onConfigureProvider,
  onRefresh,
  onSync,
}: OptionChainTableProps) {
  const { t } = useTranslation();
  const [moneyness, setMoneyness] = useState<MoneynessFilter>("near");
  const [selectedSymbol, setSelectedSymbol] = useState<string>("");
  const [selectedQuoteField, setSelectedQuoteField] = useState<SelectedQuoteField>("last");
  const [columnPreset, setColumnPreset] = useState<ColumnPreset>("essential");
  const underlyingPrice = null;
  const columns = COLUMN_PRESETS[columnPreset];
  const rows = useMemo(() => groupOptionSnapshots(snapshots, underlyingPrice), [snapshots, underlyingPrice]);
  const visibleRows = useMemo(
    () => filterRowsByMoneyness(rows, moneyness, underlyingPrice),
    [rows, moneyness, underlyingPrice],
  );
  const tableColumns = useMemo(
    () => buildOptionTableColumns(columns, selectedSymbol, underlyingPrice, handleSelectContract, t("options.strike")),
    [columns, selectedSymbol, underlyingPrice, t],
  );
  const table = useReactTable({
    data: visibleRows,
    columns: tableColumns,
    getCoreRowModel: getCoreRowModel(),
  });
  const selectedContract = snapshots.find((snapshot) => snapshot.option_symbol === selectedSymbol) ?? null;
  const totalVolume = snapshots.reduce((sum, snapshot) => sum + snapshot.volume, 0);
  const totalOpenInterest = snapshots.reduce((sum, snapshot) => sum + (snapshot.open_interest ?? 0), 0);
  const latestTimestamp = snapshots[0]?.timestamp;
  const averageIv = average(snapshots.map((snapshot) => snapshot.implied_volatility));
  const surface = useMemo(() => buildOptionSurface(snapshots), [snapshots]);
  const contractUniverse = useMemo(() => buildContractUniverse(contracts), [contracts]);
  const availableExpiries = contractUniverse.expiries;
  const activeExpiry = buildExpiryMeta(expiry);
  const expiryTabs = buildExpiryTabs(expiry);

  function handleSelectContract(symbol: string, quoteField: SelectedQuoteField) {
    setSelectedSymbol(symbol);
    setSelectedQuoteField(quoteField);
    onSelectedContractChange(symbol);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("options.title")}</CardTitle>
        <CardAction className="flex gap-2">
          <Button type="button" variant="outline" onClick={onRefresh} disabled={loading || syncing}>
            {loading ? t("options.loading") : t("options.refresh")}
          </Button>
          <Button type="button" onClick={onSync} disabled={loading || syncing}>
            {syncing ? t("options.syncing") : t("options.syncCurrent", { symbol: underlying })}
          </Button>
        </CardAction>
      </CardHeader>

      <CardContent>
      <div className="grid grid-cols-4 gap-3 max-lg:grid-cols-2 max-sm:grid-cols-1">
        <Metric label="Underlying" value={underlying} />
        <Metric label={t("options.referencePrice")} value={underlyingPrice ? formatOptionNumber(underlyingPrice) : "-"} />
        <Metric label="IV" value={formatOptionPercent(averageIv)} />
        <Metric label={t("options.mode")} value="Single Underlying" />
      </div>

      <div className="mt-4 grid grid-cols-3 gap-3 max-lg:grid-cols-1">
        {readiness ? (
          <ReadinessCard
            label={t("options.providerReadiness")}
            value={readiness.ready ? t("options.ready") : t("options.notReady")}
            status={readiness.ready ? "ready" : "not-ready"}
            detail={readiness.ready ? readiness.message : readiness.missing.length > 0 ? t("options.missing", { items: readiness.missing.join(", ") }) : readiness.message}
          />
        ) : (
          <ReadinessCard label={t("options.providerReadiness")} value={t("options.checking")} status="missing" detail={t("options.waitingProvider")} />
        )}
        {syncHealth ? (
          <ReadinessCard label={t("options.syncHealth")} value={healthStatusLabel(syncHealth.status, t)} status={syncHealth.status} detail={syncHealth.message} />
        ) : (
          <ReadinessCard label={t("options.syncHealth")} value={t("options.checking")} status="missing" detail={t("options.waitingSync")} />
        )}
        <ReadinessCard
          label={t("options.latestRun")}
          value={latestSyncRun?.status && latestSyncRun.status !== "empty" ? latestSyncRun.status : t("options.noRecord")}
          status={latestSyncRun?.status ?? "missing"}
          detail={latestSyncRun ? formatSyncRunDetail(latestSyncRun) : t("options.noLatestSync")}
        />
      </div>

      <div className="mt-4 grid grid-cols-[minmax(140px,180px)_minmax(150px,190px)_minmax(220px,auto)_minmax(230px,1fr)] items-end gap-3 max-xl:grid-cols-2 max-sm:grid-cols-1">
        <label className="flex flex-col gap-1.5">
          <span className="text-xs text-muted-foreground">Underlying</span>
          <div className="flex h-10 items-center rounded-md border bg-muted/40 px-3 text-sm font-semibold">
            {underlying}
          </div>
        </label>
        <label className="flex flex-col gap-1.5">
          <span className="text-xs text-muted-foreground">{t("options.expiry")}</span>
          <Input type="date" value={expiry} onChange={(event) => onExpiryChange(event.target.value)} />
        </label>
        <ToggleGroup
          type="single"
          value={moneyness}
          variant="outline"
          size="sm"
          spacing={0}
          className="self-end"
          aria-label={t("options.filterLabel")}
          onValueChange={(value) => {
            if (value) setMoneyness(value as MoneynessFilter);
          }}
        >
          {[
            ["near", t("options.moneynessNear")],
            ["all", t("options.moneynessAll")],
            ["itm", t("options.moneynessItm")],
            ["otm", t("options.moneynessOtm")],
          ].map(([value, label]) => (
            <ToggleGroupItem
              key={value}
              value={value}
            >
              {label}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
        <ToggleGroup
          type="single"
          value={columnPreset}
          variant="outline"
          size="sm"
          spacing={0}
          className="self-end"
          aria-label={t("options.columnPreset")}
          onValueChange={(value) => {
            if (value) setColumnPreset(value as ColumnPreset);
          }}
        >
          {[
            ["essential", t("options.presetEssential")],
            ["greeks", t("options.presetGreeks")],
            ["liquidity", t("options.presetLiquidity")],
          ].map(([value, label]) => (
            <ToggleGroupItem
              key={value}
              value={value}
            >
              {label}
            </ToggleGroupItem>
          ))}
        </ToggleGroup>
      </div>

      <div className="mt-4 flex gap-2 overflow-x-auto pb-1" aria-label={t("options.expiry")}>
        {expiryTabs.map((expiryMeta) => (
          <Button
            key={expiryMeta.label}
            type="button"
            variant={expiryMeta.label === expiry ? "secondary" : "outline"}
            size="sm"
            className="h-auto gap-2 py-2"
            onClick={() => onExpiryChange(expiryMeta.label)}
          >
            <span className="font-semibold">{expiryMeta.label}</span>
            <span className="text-muted-foreground">{expiryMeta.daysLabel}</span>
            <span className="text-muted-foreground">{expiryMeta.kind}</span>
          </Button>
        ))}
      </div>

	      <div className="mt-4 grid grid-cols-4 gap-3 max-lg:grid-cols-2 max-sm:grid-cols-1">
	        <Metric label={t("options.contracts")} value={snapshots.length.toLocaleString()} />
	        <Metric label="Volume" value={totalVolume.toLocaleString()} />
	        <Metric label="Open Interest" value={totalOpenInterest.toLocaleString()} />
	        <Metric label={t("options.updatedAt")} value={latestTimestamp ? new Date(latestTimestamp).toLocaleString() : "-"} />
	      </div>

      <OptionsSurfacePanel surface={surface} labels={{
	        title: t("options.surface.title"),
	        callVolume: t("options.surface.callVolume"),
	        putVolume: t("options.surface.putVolume"),
	        putCall: t("options.surface.putCall"),
	        avgDelta: t("options.surface.avgDelta"),
	        avgGamma: t("options.surface.avgGamma"),
	        avgTheta: t("options.surface.avgTheta"),
	        avgVega: t("options.surface.avgVega"),
	        liquidity: t("options.surface.liquidity"),
	        greeks: t("options.surface.greeks"),
	      }} />

      <ContractUniversePanel
        universe={contractUniverse}
        loading={contractsLoading}
        error={contractsError}
        labels={{
          title: t("options.contractUniverse.title"),
          calls: t("options.contractUniverse.calls"),
          puts: t("options.contractUniverse.puts"),
          expiries: t("options.contractUniverse.expiries"),
          strikeRange: t("options.contractUniverse.strikeRange"),
          source: t("options.contractUniverse.source"),
          metadataReady: t("options.contractUniverse.metadataReady"),
          metadataMissing: t("options.contractUniverse.metadataMissing"),
          loading: t("options.contractUniverse.loading"),
        }}
      />

	      {error ? (
        <Alert variant="destructive" className="mb-3">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      {!error && !loading && snapshots.length === 0 ? (
        <OptionsEmptyState
          underlying={underlying}
          expiry={expiry}
          readiness={readiness}
          syncHealth={syncHealth}
          latestSyncRun={latestSyncRun}
          contractsCount={contracts.length}
          availableExpiries={availableExpiries}
          syncing={syncing}
          onConfigureProvider={onConfigureProvider}
          onRefresh={onRefresh}
          onSync={onSync}
        />
      ) : (
      <div className="mt-4 grid grid-cols-[minmax(0,1fr)_280px] items-start gap-4 max-xl:grid-cols-1">
        <div className="overflow-x-auto rounded-lg border">
          {visibleRows.length > 0 ? (
            <Table className="min-w-[1160px] text-xs">
              <TableHeader>
                {table.getHeaderGroups().map((headerGroup) => (
                  <TableRow key={headerGroup.id}>
                    {headerGroup.headers.map((header) => (
                      <TableHead
                        key={header.id}
                        colSpan={header.colSpan}
                        className={optionHeaderClass(header.id)}
                      >
                        {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                      </TableHead>
                    ))}
                  </TableRow>
                ))}
              </TableHeader>
              <TableBody>
                {table.getRowModel().rows.map((row) => (
                  <Fragment key={row.id}>
                    {row.original.isAtTheMoney && underlyingPrice !== null ? (
                      <TableRow>
                        <TableCell className="bg-secondary px-3 py-2 text-center text-xs font-semibold text-secondary-foreground" colSpan={columns.call.length + columns.put.length + 1}>
                          {t("options.currentPriceNear", { price: formatOptionNumber(underlyingPrice) })}
                        </TableCell>
                      </TableRow>
                    ) : null}
                    <TableRow className={row.original.isAtTheMoney ? "border-t-2 border-dashed border-primary bg-muted/40" : ""}>
                      {row.getVisibleCells().map((cell) => (
                        <TableCell key={cell.id} className={optionCellClass(cell.column.id, row.original, underlyingPrice)}>
                          {flexRender(cell.column.columnDef.cell, cell.getContext())}
                        </TableCell>
                      ))}
                    </TableRow>
                  </Fragment>
                ))}
              </TableBody>
            </Table>
          ) : (
            <div className="flex min-h-[142px] items-center rounded-lg border border-dashed p-4 text-sm text-muted-foreground">{t("options.noRows")}</div>
          )}
        </div>

        <aside className="rounded-lg border bg-muted/40 p-4">
          <div className="mb-3 flex items-start justify-between gap-3">
            <div>
              <h3 className="text-base font-semibold">{t("options.contractQuote")}</h3>
              <p className="mt-1 text-xs text-muted-foreground">{t("options.quoteOnly")}</p>
            </div>
            <Badge variant="outline">{quoteFieldLabel(selectedQuoteField, t)}</Badge>
          </div>
          {selectedContract ? (
            <>
              <div className="mb-3 flex flex-wrap gap-2">
                <Badge variant="outline">{inferOptionSideLabel(selectedContract)}</Badge>
                <Badge variant="outline">{formatOptionExpiry(selectedContract)}</Badge>
                <Badge variant="outline">{formatOptionStrike(selectedContract)}</Badge>
              </div>
              <dl className="grid grid-cols-[86px_minmax(0,1fr)] gap-x-3 gap-y-2 text-xs">
                <Detail label={t("options.contract")} value={selectedContract.option_symbol} />
                <Detail label="Underlying" value={selectedContract.underlying_symbol} />
                <Detail label="Timestamp" value={new Date(selectedContract.timestamp).toLocaleString()} />
                <Detail
                  label="Bid / Ask"
                  value={`${formatOptionNumber(selectedContract.bid)} / ${formatOptionNumber(selectedContract.ask)}`}
                />
                <Detail label="Last" value={formatOptionNumber(selectedContract.last)} />
                <Detail label="IV" value={formatOptionPercent(selectedContract.implied_volatility)} />
                <Detail label="Delta" value={formatOptionNumber(selectedContract.delta, 4)} />
                <Detail label="Gamma" value={formatOptionNumber(selectedContract.gamma, 4)} />
                <Detail label="Theta" value={formatOptionNumber(selectedContract.theta, 4)} />
                <Detail label="Vega" value={formatOptionNumber(selectedContract.vega, 4)} />
                <Detail label="Volume" value={selectedContract.volume.toLocaleString()} />
                <Detail label="OI" value={selectedContract.open_interest?.toLocaleString() ?? "-"} />
                <Detail label="Source" value={selectedContract.source} />
              </dl>
              <div className="mt-4 border-t pt-3">
                <span className="text-xs text-muted-foreground">{t("options.premium")}</span>
                <strong className="mt-1 block text-lg">{estimatePremium(selectedContract, selectedQuoteField)}</strong>
              </div>
              <OptionBarsPanel
                bars={selectedBars}
                loading={selectedBarsLoading}
                error={selectedBarsError}
                timeframe={selectedBarsTimeframe}
                onTimeframeChange={onSelectedBarsTimeframeChange}
                labels={{
                  title: t("options.optionBars"),
                  waiting: t("options.waiting"),
                  loading: t("options.loadingBars"),
                  empty: t("options.noBars"),
                }}
              />
            </>
          ) : (
            <p className="text-sm leading-6 text-muted-foreground">{t("options.selectContractHint")}</p>
          )}
        </aside>
      </div>
      )}
      </CardContent>
    </Card>
  );
}

function buildOptionTableColumns(
  columns: { call: OptionColumn[]; put: OptionColumn[] },
  selectedSymbol: string,
  underlyingPrice: number | null,
  onSelect: (symbol: string, quoteField: SelectedQuoteField) => void,
  strikeLabel: string,
): ColumnDef<OptionChainRow>[] {
  return [
    {
      id: "call",
      header: "Call",
      columns: columns.call.map((column) => ({
        id: `call-${column}`,
        header: COLUMN_LABELS[column],
        cell: ({ row }) => (
          <OptionCellContent
            column={column}
            snapshot={row.original.call}
            selectedSymbol={selectedSymbol}
            onSelect={onSelect}
          />
        ),
      })),
    },
    {
      id: "strike",
      header: "Strike",
      columns: [
        {
          id: "strike-price",
          header: strikeLabel,
          cell: ({ row }) => formatOptionNumber(row.original.strike),
        },
      ],
    },
    {
      id: "put",
      header: "Put",
      columns: columns.put.map((column) => ({
        id: `put-${column}`,
        header: COLUMN_LABELS[column],
        cell: ({ row }) => (
          <OptionCellContent
            column={column}
            snapshot={row.original.put}
            selectedSymbol={selectedSymbol}
            onSelect={onSelect}
          />
        ),
      })),
    },
  ];
}

function OptionCellContent({
  column,
  snapshot,
  selectedSymbol,
  onSelect,
}: {
  column: OptionColumn;
  snapshot?: OptionSnapshot;
  selectedSymbol: string;
  onSelect: (symbol: string, quoteField: SelectedQuoteField) => void;
}) {
  if (column === "bid") {
    return <QuoteCell snapshot={snapshot} value={snapshot?.bid} quoteField="bid" onSelect={onSelect} />;
  }
  if (column === "ask") {
    return <QuoteCell snapshot={snapshot} value={snapshot?.ask} quoteField="ask" onSelect={onSelect} />;
  }
  if (column === "last") {
    return <QuoteCell snapshot={snapshot} value={snapshot?.last} quoteField="last" onSelect={onSelect} />;
  }

  if (column === "delta") {
    return (
      <span className={snapshot?.option_symbol === selectedSymbol ? "font-semibold text-primary" : undefined}>
        {formatOptionNumber(snapshot?.delta, 4)}
      </span>
    );
  }
  if (column === "iv") return formatOptionPercent(snapshot?.implied_volatility);
  if (column === "oi") return snapshot?.open_interest?.toLocaleString() ?? "-";
  return snapshot?.volume.toLocaleString() ?? "-";
}

function QuoteCell({
  snapshot,
  value,
  quoteField,
  onSelect,
}: {
  snapshot?: OptionSnapshot;
  value: number | null | undefined;
  quoteField: SelectedQuoteField;
  onSelect: (symbol: string, quoteField: SelectedQuoteField) => void;
}) {
  if (!snapshot) return "-";
  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      className="h-auto w-full justify-end p-0 text-xs font-semibold text-primary hover:bg-transparent"
      onClick={() => onSelect(snapshot.option_symbol, quoteField)}
      title={quoteFieldLabel(quoteField)}
    >
      {formatOptionNumber(value)}
    </Button>
  );
}

function optionHeaderClass(headerId: string) {
  if (headerId === "call") return "text-center font-semibold text-primary";
  if (headerId === "put") return "text-center font-semibold text-muted-foreground";
  if (headerId === "strike" || headerId === "strike-price") return "bg-muted text-center font-semibold text-foreground";
  return "text-right";
}

function optionCellClass(columnId: string, row: OptionChainRow, underlyingPrice: number | null) {
  if (columnId === "strike-price") return "bg-muted text-center font-semibold text-foreground";
  if (columnId.startsWith("call-")) return cn("text-right tabular-nums", getMoneynessClass("call", row.strike, underlyingPrice));
  if (columnId.startsWith("put-")) return cn("text-right tabular-nums", getMoneynessClass("put", row.strike, underlyingPrice));
  return "text-right tabular-nums";
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border bg-card p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 truncate text-base font-semibold">{value}</p>
    </div>
  );
}

type OptionSurface = {
  callVolume: number;
  putVolume: number;
  putCallRatio: number | null;
  avgDelta: number | null;
  avgGamma: number | null;
  avgTheta: number | null;
  avgVega: number | null;
  liquidContracts: number;
};

type ContractUniverse = {
  total: number;
  calls: number;
  puts: number;
  expiries: string[];
  minStrike: number | null;
  maxStrike: number | null;
  sources: string[];
};

function OptionsSurfacePanel({
  surface,
  labels,
}: {
  surface: OptionSurface;
  labels: Record<
    "title" | "callVolume" | "putVolume" | "putCall" | "avgDelta" | "avgGamma" | "avgTheta" | "avgVega" | "liquidity" | "greeks",
    string
  >;
}) {
  return (
    <div className="mt-4 rounded-lg border bg-muted/30 p-3">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold">{labels.title}</h3>
        </div>
        <div className="flex flex-wrap gap-2">
          <Badge variant="secondary">{labels.liquidity}</Badge>
          <Badge variant="outline">{labels.greeks}</Badge>
        </div>
      </div>
      <div className="grid grid-cols-7 gap-2 max-2xl:grid-cols-4 max-lg:grid-cols-2 max-sm:grid-cols-1">
        <SurfaceMetric label={labels.callVolume} value={surface.callVolume.toLocaleString()} />
        <SurfaceMetric label={labels.putVolume} value={surface.putVolume.toLocaleString()} />
        <SurfaceMetric label={labels.putCall} value={surface.putCallRatio === null ? "-" : surface.putCallRatio.toFixed(2)} />
        <SurfaceMetric label={labels.avgDelta} value={formatOptionNumber(surface.avgDelta, 4)} />
        <SurfaceMetric label={labels.avgGamma} value={formatOptionNumber(surface.avgGamma, 4)} />
        <SurfaceMetric label={labels.avgTheta} value={formatOptionNumber(surface.avgTheta, 4)} />
        <SurfaceMetric label={labels.avgVega} value={formatOptionNumber(surface.avgVega, 4)} />
      </div>
      <div className="mt-3 rounded-lg border bg-background px-3 py-2 text-xs text-muted-foreground">
        {labels.liquidity}: <strong className="text-foreground">{surface.liquidContracts.toLocaleString()}</strong>
      </div>
    </div>
  );
}

function ContractUniversePanel({
  universe,
  loading,
  error,
  labels,
}: {
  universe: ContractUniverse;
  loading: boolean;
  error: string | null;
  labels: Record<
    "title" | "calls" | "puts" | "expiries" | "strikeRange" | "source" | "metadataReady" | "metadataMissing" | "loading",
    string
  >;
}) {
  const strikeRange =
    universe.minStrike === null || universe.maxStrike === null
      ? "-"
      : `${formatOptionNumber(universe.minStrike)} - ${formatOptionNumber(universe.maxStrike)}`;
  const source = universe.sources.length > 0 ? universe.sources.join(", ") : "-";

  return (
    <div className="mt-4 rounded-lg border bg-card p-3">
      <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold">{labels.title}</h3>
        </div>
        <Badge variant={universe.total > 0 ? "secondary" : "outline"}>
          {loading ? labels.loading : universe.total > 0 ? labels.metadataReady : labels.metadataMissing}
        </Badge>
      </div>
      {error ? <p className="mb-3 text-sm text-destructive">{error}</p> : null}
      <div className="grid grid-cols-5 gap-2 max-xl:grid-cols-3 max-md:grid-cols-2 max-sm:grid-cols-1">
        <SurfaceMetric label={labels.calls} value={universe.calls.toLocaleString()} />
        <SurfaceMetric label={labels.puts} value={universe.puts.toLocaleString()} />
        <SurfaceMetric label={labels.expiries} value={universe.expiries.length.toLocaleString()} />
        <SurfaceMetric label={labels.strikeRange} value={strikeRange} />
        <SurfaceMetric label={labels.source} value={source} />
      </div>
      {universe.expiries.length > 0 ? (
        <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
          {universe.expiries.slice(0, 8).map((expiry) => (
            <Badge key={expiry} variant="outline" className="shrink-0">
              {expiry}
            </Badge>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function SurfaceMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border bg-background p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 truncate text-sm font-semibold tabular-nums">{value}</p>
    </div>
  );
}

function OptionsEmptyState({
  underlying,
  expiry,
  readiness,
  syncHealth,
  latestSyncRun,
  contractsCount,
  availableExpiries,
  syncing,
  onConfigureProvider,
  onRefresh,
  onSync,
}: {
  underlying: string;
  expiry: string;
  readiness: ProviderReadiness | null;
  syncHealth: ProviderSyncHealth | null;
  latestSyncRun: ProviderSyncRunItem | null;
  contractsCount: number;
  availableExpiries: string[];
  syncing: boolean;
  onConfigureProvider: () => void;
  onRefresh: () => void;
  onSync: () => void;
}) {
  const { t } = useTranslation();
  const canSync = Boolean(readiness?.ready) && !syncing;

  return (
    <div className="mt-4 rounded-lg border border-dashed bg-card p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-2xl">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">{underlying}</Badge>
            <Badge variant="outline">{expiry}</Badge>
            <Badge variant={readiness?.ready ? "secondary" : "destructive"}>
              {readiness?.ready ? t("options.ready") : t("options.notReady")}
            </Badge>
          </div>
          <h3 className="mt-3 text-base font-semibold">{t("options.emptyTitle")}</h3>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            {contractsCount > 0
              ? t("options.emptyWithContractsDescription", { count: contractsCount.toLocaleString(), symbol: underlying, expiry })
              : t("options.emptyDescription", { symbol: underlying, expiry })}
          </p>
          {availableExpiries.length > 0 && !availableExpiries.includes(expiry) ? (
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              {t("options.availableExpiries", { symbol: underlying, expiries: availableExpiries.join(", ") })}
            </p>
          ) : null}
        </div>
        <div className="flex flex-wrap gap-2">
          {!readiness?.ready ? (
            <Button type="button" onClick={onConfigureProvider}>
              {t("options.configureProvider")}
            </Button>
          ) : null}
          <Button type="button" variant="outline" onClick={onRefresh}>
            {t("options.refresh")}
          </Button>
          <Button type="button" variant={readiness?.ready ? "default" : "outline"} onClick={onSync} disabled={!canSync}>
            {syncing ? t("options.syncing") : t("options.syncCurrent", { symbol: underlying })}
          </Button>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-3 max-lg:grid-cols-1">
        <StatusCardLite
          label={t("options.providerReadiness")}
          value={readiness?.ready ? t("options.ready") : t("options.notReady")}
          detail={readiness?.message ?? t("options.waitingProvider")}
        />
        <StatusCardLite
          label={t("options.syncHealth")}
          value={syncHealth ? healthStatusLabel(syncHealth.status, t) : t("options.noRecord")}
          detail={syncHealth?.message ?? t("options.waitingSync")}
        />
        <StatusCardLite
          label={t("options.latestRun")}
          value={latestSyncRun?.status && latestSyncRun.status !== "empty" ? latestSyncRun.status : t("options.noRecord")}
          detail={latestSyncRun ? formatSyncRunDetail(latestSyncRun) : t("options.noLatestSyncForSymbol", { symbol: underlying })}
        />
      </div>
    </div>
  );
}

function formatSyncRunDetail(run: ProviderSyncRunItem) {
  const target = [run.target_symbol, run.target_expiry].filter(Boolean).join(" · ");
  const prefix = target ? `${target} · ` : "";
  return `${prefix}${run.rows_written.toLocaleString()} rows · ${formatDate(run.finished_at ?? run.started_at)}`;
}

function StatusCardLite({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <div className="rounded-lg border bg-background p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm font-semibold">{value}</p>
      <p className="mt-2 text-xs leading-5 text-muted-foreground">{detail}</p>
    </div>
  );
}

function ReadinessCard({ label, value, status, detail }: { label: string; value: string; status: string; detail: string }) {
  const borderClass = ["ready", "ok", "succeeded"].includes(status)
    ? "border-l-primary"
    : ["failing", "failed", "error"].includes(status)
      ? "border-l-destructive"
      : "border-l-muted-foreground";

  return (
    <div className={cn("rounded-lg border border-l-4 bg-card p-3", borderClass)}>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-sm font-semibold">{value}</p>
      <p className="mt-2 break-words text-xs leading-5 text-muted-foreground">{detail}</p>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="min-w-0 break-words font-semibold text-foreground">{value}</dd>
    </>
  );
}

function OptionBarsPanel({
  bars,
  loading,
  error,
  timeframe,
  onTimeframeChange,
  labels,
}: {
  bars: OptionBar[];
  loading: boolean;
  error: string | null;
  timeframe: MarketTimeframe;
  onTimeframeChange: (timeframe: MarketTimeframe) => void;
  labels: {
    title: string;
    waiting: string;
    loading: string;
    empty: string;
  };
}) {
  const latest = bars[bars.length - 1];
  return (
    <div className="mt-4 grid gap-3 rounded-lg border border-dashed bg-card p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">{labels.title}</p>
          <p className="mt-1 text-xs text-muted-foreground">{latest ? `${latest.source} · ${bars.length} bars` : labels.waiting}</p>
        </div>
        <ToggleGroup
          type="single"
          value={timeframe}
          variant="outline"
          size="sm"
          spacing={0}
          onValueChange={(value) => {
            if (value === "1m" || value === "5m" || value === "1d") onTimeframeChange(value);
          }}
        >
          <ToggleGroupItem value="1m">1m</ToggleGroupItem>
          <ToggleGroupItem value="5m">5m</ToggleGroupItem>
          <ToggleGroupItem value="1d">1d</ToggleGroupItem>
        </ToggleGroup>
      </div>
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
      {loading ? <p className="text-sm text-muted-foreground">{labels.loading}</p> : null}
      {!loading && bars.length === 0 ? <p className="text-sm text-muted-foreground">{labels.empty}</p> : null}
      {bars.length > 0 ? (
        <>
          <OptionBarsCandles bars={bars} />
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary">Close {latest.close.toFixed(2)}</Badge>
            <Badge variant="outline">Vol {latest.volume.toLocaleString()}</Badge>
          </div>
        </>
      ) : null}
    </div>
  );
}

function OptionBarsCandles({ bars }: { bars: OptionBar[] }) {
  const candles = optionBarsCandleGeometry(bars);
  if (candles.length < 2) return <div className="h-11 w-full rounded-md bg-muted/50" />;
  return (
    <svg className="h-11 w-full rounded-md bg-muted/50" viewBox="0 0 160 44" role="img" aria-label="selected option candlestick chart">
      {candles.map((candle) => {
        const color = candle.close >= candle.open ? MARKET_COLORS.up : MARKET_COLORS.down;
        return (
          <g key={candle.key}>
            <line x1={candle.x} x2={candle.x} y1={candle.highY} y2={candle.lowY} stroke={color} strokeWidth="1.2" />
            <rect
              x={candle.bodyX}
              y={candle.bodyY}
              width={candle.bodyWidth}
              height={candle.bodyHeight}
              rx="1"
              fill={color}
            />
          </g>
        );
      })}
    </svg>
  );
}

function optionBarsCandleGeometry(bars: OptionBar[]) {
  const source = bars.slice(-20);
  if (source.length < 2) return [];
  const min = Math.min(...source.map((bar) => bar.low));
  const max = Math.max(...source.map((bar) => bar.high));
  const spread = max - min || 1;
  const step = 160 / source.length;
  const bodyWidth = Math.max(2, Math.min(6, step * 0.52));
  const y = (value: number) => 5 + (1 - (value - min) / spread) * 34;

  return source.map((bar, index) => {
    const x = step * index + step / 2;
    const openY = y(bar.open);
    const closeY = y(bar.close);
    return {
      key: `${bar.timestamp}:${bar.source}`,
      x,
      highY: y(bar.high),
      lowY: y(bar.low),
      open: bar.open,
      close: bar.close,
      bodyX: x - bodyWidth / 2,
      bodyY: Math.min(openY, closeY),
      bodyWidth,
      bodyHeight: Math.max(2, Math.abs(openY - closeY)),
    };
  });
}

function average(values: Array<number | null | undefined>) {
  const numbers = values.filter((value): value is number => typeof value === "number" && Number.isFinite(value));
  if (numbers.length === 0) return null;
  return numbers.reduce((sum, value) => sum + value, 0) / numbers.length;
}

function buildOptionSurface(snapshots: OptionSnapshot[]): OptionSurface {
  const calls = snapshots.filter((snapshot) => optionSide(snapshot) === "call");
  const puts = snapshots.filter((snapshot) => optionSide(snapshot) === "put");
  const callVolume = calls.reduce((sum, snapshot) => sum + snapshot.volume, 0);
  const putVolume = puts.reduce((sum, snapshot) => sum + snapshot.volume, 0);
  const liquidContracts = snapshots.filter((snapshot) => snapshot.volume > 0 || (snapshot.open_interest ?? 0) > 0).length;

  return {
    callVolume,
    putVolume,
    putCallRatio: callVolume > 0 ? putVolume / callVolume : null,
    avgDelta: average(snapshots.map((snapshot) => snapshot.delta)),
    avgGamma: average(snapshots.map((snapshot) => snapshot.gamma)),
    avgTheta: average(snapshots.map((snapshot) => snapshot.theta)),
    avgVega: average(snapshots.map((snapshot) => snapshot.vega)),
    liquidContracts,
  };
}

function buildContractUniverse(contracts: OptionContract[]): ContractUniverse {
  const calls = contracts.filter((contract) => contract.option_type.toLowerCase() === "call").length;
  const puts = contracts.filter((contract) => contract.option_type.toLowerCase() === "put").length;
  const strikes = contracts.map((contract) => contract.strike).filter((strike) => Number.isFinite(strike));

  return {
    total: contracts.length,
    calls,
    puts,
    expiries: Array.from(new Set(contracts.map((contract) => contract.expiry))).sort(),
    minStrike: strikes.length > 0 ? Math.min(...strikes) : null,
    maxStrike: strikes.length > 0 ? Math.max(...strikes) : null,
    sources: Array.from(new Set(contracts.map((contract) => contract.source))).sort(),
  };
}

function optionSide(snapshot: OptionSnapshot): "call" | "put" | "unknown" {
  const symbol = snapshot.option_symbol.toUpperCase().replace(/^O:/, "");
  if (/\d{6}C\d{8}/.test(symbol)) return "call";
  if (/\d{6}P\d{8}/.test(symbol)) return "put";
  return "unknown";
}

function buildExpiryMeta(expiry: string) {
  const expiryDate = new Date(`${expiry}T00:00:00`);
  const today = new Date();
  const days = Number.isFinite(expiryDate.getTime())
    ? Math.max(0, Math.ceil((expiryDate.getTime() - today.getTime()) / 86_400_000))
    : null;
  return {
    label: expiry || "-",
    daysLabel: days === null ? "-" : `${days}d`,
    kind: days !== null && days <= 10 ? "W" : "M",
  };
}

function buildExpiryTabs(activeExpiry: string) {
  return Array.from(new Set([activeExpiry, ...nextFridayExpiries(4)]))
    .filter(Boolean)
    .sort()
    .map(buildExpiryMeta);
}

function nextFridayExpiries(count: number) {
  const expiries: string[] = [];
  const cursor = new Date();
  cursor.setHours(0, 0, 0, 0);
  const daysUntilFriday = (5 - cursor.getDay() + 7) % 7 || 7;
  cursor.setDate(cursor.getDate() + daysUntilFriday);
  for (let index = 0; index < count; index += 1) {
    expiries.push(formatLocalDate(cursor));
    cursor.setDate(cursor.getDate() + 7);
  }
  return expiries;
}

function formatLocalDate(value: Date) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function inferOptionSideLabel(snapshot: OptionSnapshot) {
  const side = optionSide(snapshot);
  if (side === "call") return "Call";
  if (side === "put") return "Put";
  return "Option";
}

function formatOptionExpiry(snapshot: OptionSnapshot) {
  const symbol = snapshot.option_symbol.toUpperCase().replace(/^O:/, "");
  const match = symbol.match(/^(.+?)(\d{6})([CP])(\d{8})$/);
  if (!match) return "Expiry -";
  const raw = match[2];
  return `20${raw.slice(0, 2)}-${raw.slice(2, 4)}-${raw.slice(4, 6)}`;
}

function formatOptionStrike(snapshot: OptionSnapshot) {
  const symbol = snapshot.option_symbol.toUpperCase().replace(/^O:/, "");
  const match = symbol.match(/^(.+?)(\d{6})([CP])(\d{8})$/);
  if (!match) return "Strike -";
  return `Strike ${formatOptionNumber(Number(match[4]) / 1000)}`;
}

function getMoneynessClass(side: "call" | "put", strike: number, underlyingPrice: number | null) {
  if (underlyingPrice === null) return "";
  const isItm = side === "call" ? strike < underlyingPrice : strike > underlyingPrice;
  return isItm ? "bg-muted/60 text-foreground" : "text-muted-foreground";
}

function quoteFieldLabel(quoteField: SelectedQuoteField, t?: (key: string) => string) {
  if (t) return t(`options.quoteField.${quoteField}`);
  const labels: Record<SelectedQuoteField, string> = {
    bid: "Inspect Bid",
    ask: "Inspect Ask",
    last: "Inspect Last",
  };
  return labels[quoteField];
}

function healthStatusLabel(status: string, t: (key: string) => string) {
  if (["ok", "stale", "failing", "missing"].includes(status)) {
    return t(`options.health.${status}`);
  }
  return status;
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function estimatePremium(snapshot: OptionSnapshot, quoteField: SelectedQuoteField) {
  const price = quoteField === "ask" ? snapshot.ask : quoteField === "bid" ? snapshot.bid : snapshot.last;
  if (typeof price !== "number" || !Number.isFinite(price)) return "-";
  return `$${formatOptionNumber(price * 100)}`;
}
