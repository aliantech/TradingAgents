import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Activity, Bot, CandlestickChart, ClipboardList, Database, FileText, FlaskConical, KeyRound, Languages, LayoutDashboard, Menu, Moon, PanelLeftClose, PanelLeftOpen, Settings, ShieldCheck, SlidersHorizontal, Sun, type LucideIcon, X, Workflow } from "lucide-react";
import {
  flexRender,
  getCoreRowModel,
  useReactTable,
  type ColumnDef,
} from "@tanstack/react-table";

import { AnalysisPanel } from "../features/analysis/AnalysisPanel";
import { DataSyncPanel } from "../features/market-data/DataSyncPanel";
import { ReportHistory } from "../features/reports/ReportHistory";
import { ReportPanel } from "../features/reports/ReportPanel";
import { StrategyLabPanel } from "../features/strategy-lab/StrategyLabPanel";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectGroup, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MetricCard, StatusCard } from "@/components/workbench/metric-card";
import { cn } from "@/lib/utils";
import { getSettingsCatalog, type SettingsCatalogSection } from "@/features/settings/settingsCatalog";
import {
  getAnalysisStatus,
  getBackendHealth,
  getMarketBars,
  getOptionBars,
  getOptionChain,
  getProviderReadiness,
  getProviderSyncHealth,
  getProviderSyncSummary,
  getReport,
  getReportComparison,
  listAnalysisRuns,
  listOptionContracts,
  listProviderSyncSummaryGroups,
  listProviderSyncRuns,
  listReports,
  listSettings,
  retryAnalysis,
  startAnalysis,
  type AnalysisRunItem,
  type AnalysisStartPayload,
  syncDailyBars,
  syncOptionChain,
  type AnalysisStatus,
  type BackendHealth,
  type MarketBar,
  type MarketTimeframe,
  type OptionBar,
  type OptionContract,
  type OptionSnapshot,
  type ProviderSyncRunItem,
  type ProviderReadiness,
  type ProviderSyncHealth,
  type ProviderSyncSummary,
  type ProviderSyncSummaryGroup,
  type ReportComparison,
  type ReportListItem,
  type ResearchReport,
  type SettingItem,
  upsertSettings,
} from "../lib/api";
import "./App.css";

type PageKey = "dashboard" | "analysis" | "reports" | "market" | "options" | "strategy" | "runs" | "settings";
type NavItem = { key: PageKey; label: string };

const NAV_ICONS: Record<PageKey, LucideIcon> = {
  dashboard: LayoutDashboard,
  analysis: Bot,
  reports: FileText,
  market: CandlestickChart,
  options: Activity,
  strategy: FlaskConical,
  runs: ClipboardList,
  settings: Settings,
};

const KlineChart = lazy(() =>
  import("../features/market-data/KlineChart").then((module) => ({ default: module.KlineChart })),
);
const OptionChainTable = lazy(() =>
  import("../features/options/OptionChainTable").then((module) => ({ default: module.OptionChainTable })),
);

const NAV_KEYS: PageKey[] = ["dashboard", "analysis", "reports", "market", "options", "strategy", "runs", "settings"];

const DEFAULT_ANALYSIS_DATE = new Date().toISOString().slice(0, 10);
const SUPPORTED_SYMBOLS = ["SPY", "QQQ", "SPX", "VIX", "AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "META"];
const WATCHLIST_SETTING_KEY = "research.watchlist";
const MARKET_PULSE_SYMBOLS = ["SPY", "QQQ", "SPX", "VIX"];
const MARKET_COLORS = {
  up: "#16a34a",
  down: "#dc2626",
};

function pageFromLocationHash(): PageKey {
  const page = window.location.hash.replace(/^#/, "") as PageKey;
  return NAV_KEYS.includes(page) ? page : "dashboard";
}

function normalizeWatchlist(symbols: string[]) {
  const seen = new Set<string>();
  return symbols
    .map((item) => item.trim().toUpperCase())
    .filter((item) => SUPPORTED_SYMBOLS.includes(item))
    .filter((item) => {
      if (seen.has(item)) return false;
      seen.add(item);
      return true;
    })
    .slice(0, 10);
}

function parseWatchlistSetting(value: string | null) {
  const parsed = normalizeWatchlist(value?.split(",") ?? []);
  return parsed.length > 0 ? parsed : SUPPORTED_SYMBOLS.slice(0, 6);
}

function serializeWatchlist(symbols: string[]) {
  return normalizeWatchlist(symbols).join(",");
}

export function App() {
  const { t, i18n } = useTranslation();
  const [activePage, setActivePage] = useState<PageKey>(() => pageFromLocationHash());
  const [symbol, setSymbol] = useState("SPY");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisConfig, setAnalysisConfig] = useState<
    Pick<AnalysisStartPayload, "analysisDate" | "llmProvider" | "model" | "depth" | "analystSet" | "researchTemplate">
  >({
    analysisDate: DEFAULT_ANALYSIS_DATE,
    llmProvider: "openai",
    model: "gpt-5.5",
    depth: "standard",
    analystSet: "macro-options",
    researchTemplate: "general",
  });
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus | null>(null);
  const [analysisRuns, setAnalysisRuns] = useState<AnalysisRunItem[]>([]);
  const [backendHealth, setBackendHealth] = useState<BackendHealth | null>(null);
  const [backendHealthError, setBackendHealthError] = useState<string | null>(null);
  const [activeReport, setActiveReport] = useState<ResearchReport | null>(null);
  const [activeReportComparison, setActiveReportComparison] = useState<ReportComparison | null>(null);
  const [reports, setReports] = useState<ReportListItem[]>([]);
  const [bars, setBars] = useState<MarketBar[]>([]);
  const [marketTimeframe, setMarketTimeframe] = useState<MarketTimeframe>("1d");
  const [marketLoading, setMarketLoading] = useState(false);
  const [marketError, setMarketError] = useState<string | null>(null);
  const [marketPulseBars, setMarketPulseBars] = useState<Record<string, MarketBar[]>>({});
  const [optionSnapshots, setOptionSnapshots] = useState<OptionSnapshot[]>([]);
  const [optionContracts, setOptionContracts] = useState<OptionContract[]>([]);
  const [optionContractsLoading, setOptionContractsLoading] = useState(false);
  const [optionContractsError, setOptionContractsError] = useState<string | null>(null);
  const [optionUnderlying, setOptionUnderlying] = useState("SPX");
  const [optionExpiry, setOptionExpiry] = useState("2026-06-17");
  const [optionsLoading, setOptionsLoading] = useState(false);
  const [optionsSyncing, setOptionsSyncing] = useState(false);
  const [optionsError, setOptionsError] = useState<string | null>(null);
  const [selectedOptionSymbol, setSelectedOptionSymbol] = useState("");
  const [selectedOptionBars, setSelectedOptionBars] = useState<OptionBar[]>([]);
  const [selectedOptionBarsLoading, setSelectedOptionBarsLoading] = useState(false);
  const [selectedOptionBarsError, setSelectedOptionBarsError] = useState<string | null>(null);
  const [selectedOptionBarsTimeframe, setSelectedOptionBarsTimeframe] = useState<MarketTimeframe>("1m");
  const [syncRuns, setSyncRuns] = useState<ProviderSyncRunItem[]>([]);
  const [syncSummary, setSyncSummary] = useState<ProviderSyncSummary | null>(null);
  const [syncGroups, setSyncGroups] = useState<ProviderSyncSummaryGroup[]>([]);
  const [syncHealth, setSyncHealth] = useState<ProviderSyncHealth | null>(null);
  const [providerReadiness, setProviderReadiness] = useState<ProviderReadiness | null>(null);
  const [optionsSyncHealth, setOptionsSyncHealth] = useState<ProviderSyncHealth | null>(null);
  const [optionsProviderReadiness, setOptionsProviderReadiness] = useState<ProviderReadiness | null>(null);
  const [latestOptionsSyncRun, setLatestOptionsSyncRun] = useState<ProviderSyncRunItem | null>(null);
  const [syncProviderFilter, setSyncProviderFilter] = useState("");
  const [syncTypeFilter, setSyncTypeFilter] = useState("");
  const [syncStartedAfterFilter, setSyncStartedAfterFilter] = useState("");
  const [syncStartedBeforeFilter, setSyncStartedBeforeFilter] = useState("");
  const [syncLoading, setSyncLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [watchlist, setWatchlist] = useState<string[]>(SUPPORTED_SYMBOLS.slice(0, 6));
  const [watchlistSaving, setWatchlistSaving] = useState(false);
  const [watchlistError, setWatchlistError] = useState<string | null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">(() => {
    const savedTheme = window.localStorage.getItem("aquantlens-theme");
    if (savedTheme === "light" || savedTheme === "dark") return savedTheme;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });
  const navItems = useMemo<NavItem[]>(
    () =>
      NAV_KEYS.map((key) => ({
        key,
        label: t(`nav.${key}.label`),
      })),
    [t],
  );
  const marketSession = getMarketSessionState(t);

  useEffect(() => {
    void loadInitialState();
  }, []);

  useEffect(() => {
    const handleHashChange = () => setActivePage(pageFromLocationHash());
    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    window.localStorage.setItem("aquantlens-theme", theme);
  }, [theme]);

  function navigateToPage(page: PageKey) {
    setActivePage(page);
    if (window.location.hash !== `#${page}`) {
      window.history.replaceState(null, "", `#${page}`);
    }
  }

  function toggleLanguage() {
    void i18n.changeLanguage(i18n.language === "zh" ? "en" : "zh");
  }

  function toggleTheme() {
    setTheme((current) => (current === "dark" ? "light" : "dark"));
  }

  async function loadInitialState() {
    await Promise.allSettled([
      loadMarketContext(symbol, marketTimeframe),
      refreshMarketPulse(),
      loadOptionChain(optionUnderlying, optionExpiry),
      refreshBackendHealth(),
      refreshReports(),
      refreshAnalysisRuns(),
      loadResearchWatchlist(),
    ]);
    await refreshSyncRuns();
  }

  async function loadResearchWatchlist() {
    setWatchlistError(null);
    try {
      const response = await listSettings();
      const item = response.items.find((setting) => setting.key === WATCHLIST_SETTING_KEY);
      setWatchlist(parseWatchlistSetting(item?.value ?? null));
    } catch (caught) {
      setWatchlistError(caught instanceof Error ? caught.message : t("dashboard.watchlistLoadError"));
    }
  }

  async function saveResearchWatchlist(nextSymbols: string[]) {
    const normalized = normalizeWatchlist(nextSymbols);
    setWatchlistSaving(true);
    setWatchlistError(null);
    try {
      const response = await upsertSettings([
        {
          key: WATCHLIST_SETTING_KEY,
          value: serializeWatchlist(normalized),
          category: "user",
          is_secret: false,
        },
      ]);
      const item = response.items.find((setting) => setting.key === WATCHLIST_SETTING_KEY);
      setWatchlist(parseWatchlistSetting(item?.value ?? serializeWatchlist(normalized)));
    } catch (caught) {
      setWatchlistError(caught instanceof Error ? caught.message : t("dashboard.watchlistSaveError"));
    } finally {
      setWatchlistSaving(false);
    }
  }

  async function loadMarketContext(nextSymbol: string, timeframe = marketTimeframe) {
    setMarketLoading(true);
    setMarketError(null);
    const chartSymbol = nextSymbol.toUpperCase() === "SPX" ? "SPY" : nextSymbol;
    try {
      const barsResponse = await getMarketBars(chartSymbol, timeframe);
      setBars(barsResponse.bars);
      setMarketTimeframe(barsResponse.timeframe as MarketTimeframe);
    } catch (caught) {
      setMarketError(caught instanceof Error ? caught.message : t("market.loadError"));
    } finally {
      setMarketLoading(false);
    }
  }

  async function handleMarketTimeframeChange(timeframe: MarketTimeframe) {
    setMarketTimeframe(timeframe);
    await loadMarketContext(symbol, timeframe);
  }

  async function refreshBackendHealth() {
    setBackendHealthError(null);
    try {
      const health = await getBackendHealth();
      setBackendHealth(health);
    } catch (caught) {
      setBackendHealth(null);
      setBackendHealthError(caught instanceof Error ? caught.message : t("errors.backendHealth"));
    }
  }

  async function refreshMarketPulse() {
    const pulseResults = await Promise.allSettled(
      MARKET_PULSE_SYMBOLS.map(async (pulseSymbol) => {
        const response = await getMarketBars(pulseSymbol === "SPX" ? "SPY" : pulseSymbol, "1d");
        return [pulseSymbol, response.bars] as const;
      }),
    );
    const pulseEntries = pulseResults
      .filter((result): result is PromiseFulfilledResult<readonly [string, MarketBar[]]> => result.status === "fulfilled")
      .map((result) => result.value);
    setMarketPulseBars(Object.fromEntries(pulseEntries));
  }

  async function loadOptionChain(nextUnderlying: string, nextExpiry: string) {
    setOptionsLoading(true);
    setOptionContractsLoading(true);
    setOptionsError(null);
    setOptionContractsError(null);
    try {
      const [chainResult, contractsResult] = await Promise.allSettled([
        getOptionChain(nextUnderlying, nextExpiry),
        listOptionContracts(nextUnderlying, nextExpiry),
      ]);
      if (chainResult.status === "fulfilled") {
        setOptionSnapshots(chainResult.value.snapshots);
        setOptionUnderlying(chainResult.value.underlying_symbol);
        setOptionExpiry(chainResult.value.expiry);
      } else {
        setOptionSnapshots([]);
        setOptionUnderlying(nextUnderlying.toUpperCase());
        setOptionExpiry(nextExpiry);
        setOptionsError(chainResult.reason instanceof Error ? chainResult.reason.message : t("errors.optionsLoad"));
      }
      if (contractsResult.status === "fulfilled") {
        setOptionContracts(contractsResult.value.contracts);
      } else {
        setOptionContracts([]);
        setOptionContractsError(contractsResult.reason instanceof Error ? contractsResult.reason.message : t("errors.optionContractsLoad"));
      }
    } catch (caught) {
      setOptionsError(caught instanceof Error ? caught.message : t("errors.optionsLoad"));
    } finally {
      setOptionsLoading(false);
      setOptionContractsLoading(false);
    }
  }

  async function handleRefreshOptions() {
    await loadOptionChain(optionUnderlying, optionExpiry);
  }

  function handleOptionUnderlyingChange(value: string) {
    setOptionUnderlying(value);
    resetSelectedOptionContext();
    void loadOptionChain(value, optionExpiry);
  }

  function handleOptionExpiryChange(value: string) {
    setOptionExpiry(value);
    resetSelectedOptionContext();
    void loadOptionChain(optionUnderlying, value);
  }

  function resetSelectedOptionContext() {
    setSelectedOptionSymbol("");
    setSelectedOptionBars([]);
    setSelectedOptionBarsError(null);
  }

  async function handleSyncOptions() {
    setOptionsSyncing(true);
    setOptionsError(null);
    try {
      const response = await syncOptionChain(optionUnderlying, optionExpiry);
      if (response.status !== "succeeded") {
        setOptionsError(response.error_message ?? t("errors.optionsSyncIncomplete"));
      }
      await loadOptionChain(optionUnderlying, optionExpiry);
      await refreshSyncRuns();
    } catch (caught) {
      setOptionsError(caught instanceof Error ? caught.message : t("errors.optionsSyncTrigger"));
    } finally {
      setOptionsSyncing(false);
    }
  }

  async function loadSelectedOptionBars(optionSymbol: string, timeframe = selectedOptionBarsTimeframe) {
    if (!optionSymbol) return;
    setSelectedOptionBarsLoading(true);
    setSelectedOptionBarsError(null);
    try {
      const response = await getOptionBars(optionSymbol, timeframe);
      setSelectedOptionSymbol(response.option_symbol);
      setSelectedOptionBars(response.bars);
      setSelectedOptionBarsTimeframe(response.timeframe);
    } catch (caught) {
      setSelectedOptionBars([]);
      setSelectedOptionBarsError(caught instanceof Error ? caught.message : t("errors.optionBarsLoad"));
    } finally {
      setSelectedOptionBarsLoading(false);
    }
  }

  async function handleSelectedOptionBarsTimeframeChange(timeframe: MarketTimeframe) {
    setSelectedOptionBarsTimeframe(timeframe);
    await loadSelectedOptionBars(selectedOptionSymbol, timeframe);
  }

  async function refreshReports() {
    const reportItems = await listReports();
    setReports(reportItems);
  }

  async function refreshAnalysisRuns() {
    const response = await listAnalysisRuns();
    setAnalysisRuns(response.runs);
  }

  async function refreshSyncRuns() {
    return loadSyncRuns({ showLoading: false });
  }

  async function handleRefreshSyncRuns() {
    return loadSyncRuns({ showLoading: true });
  }

  async function handleRefreshTaskCenter() {
    await Promise.all([refreshAnalysisRuns(), loadSyncRuns({ showLoading: true })]);
  }

  function currentSyncFilters() {
    return {
      provider: syncProviderFilter.trim() || undefined,
      syncType: syncTypeFilter || undefined,
      startedAfter: toIsoDateTime(syncStartedAfterFilter),
      startedBefore: toIsoDateTime(syncStartedBeforeFilter),
    };
  }

  async function handleSyncSampleBars() {
    setSyncing(true);
    setSyncError(null);
    try {
      const response = await syncDailyBars("SPY");
      if (response.status !== "succeeded") {
        setSyncError(response.error_message ?? t("market.syncIncomplete"));
      }
      await loadSyncRuns({ showLoading: false });
      await loadMarketContext(symbol);
    } catch (caught) {
      setSyncError(caught instanceof Error ? caught.message : t("market.syncTriggerError"));
    } finally {
      setSyncing(false);
    }
  }

  async function loadSyncRuns({ showLoading }: { showLoading: boolean }) {
    if (showLoading) {
      setSyncLoading(true);
    }
    setSyncError(null);
    try {
      const filters = currentSyncFilters();
      const readinessProvider = syncProviderFilter.trim() || "polygon";
      const [response, summary, groups, health, readiness, optionHealth, optionReadiness, optionRuns] = await Promise.all([
        listProviderSyncRuns(filters),
        getProviderSyncSummary(filters),
        listProviderSyncSummaryGroups(filters),
        getProviderSyncHealth(filters),
        getProviderReadiness(readinessProvider),
        getProviderSyncHealth({ provider: "polygon", syncType: "options_chain" }),
        getProviderReadiness("polygon"),
        listProviderSyncRuns({ provider: "polygon", syncType: "options_chain" }),
      ]);
      setSyncRuns(response.runs);
      setSyncSummary(summary);
      setSyncGroups(groups.groups);
      setSyncHealth(health);
      setProviderReadiness(readiness);
      setOptionsSyncHealth(optionHealth);
      setOptionsProviderReadiness(optionReadiness);
      setLatestOptionsSyncRun(optionRuns.runs[0] ?? null);
    } catch (caught) {
      setSyncError(caught instanceof Error ? caught.message : t("market.syncHistoryError"));
    } finally {
      if (showLoading) {
        setSyncLoading(false);
      }
    }
  }

  async function handleRunAnalysis() {
    setLoading(true);
    setError(null);

    try {
      const normalizedSymbol = symbol.trim().toUpperCase();
      const status = await startAnalysis({
        symbol: normalizedSymbol,
        assetType: inferAssetType(normalizedSymbol),
        analysisDate: analysisConfig.analysisDate,
        language: i18n.language === "en" ? "en" : "zh",
        llmProvider: analysisConfig.llmProvider,
        model: analysisConfig.model,
        depth: analysisConfig.depth,
        analystSet: analysisConfig.analystSet,
        researchTemplate: analysisConfig.researchTemplate,
      });
      setAnalysisStatus(status);
      await loadMarketContext(status.symbol);
      await refreshReports();
      await refreshAnalysisRuns();
      await refreshSyncRuns();

      if (status.report_id) {
        const report = await getReport(status.report_id);
        setActiveReport(report);
        await loadReportComparison(status.report_id);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : t("errors.analysisRun"));
    } finally {
      setLoading(false);
    }
  }

  async function handleSelectReport(reportId: string) {
    setError(null);
    try {
      const report = await getReport(reportId);
      setActiveReport(report);
      await loadReportComparison(reportId);
      setSymbol(report.symbol);
      await loadMarketContext(report.symbol);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : t("errors.reportLoad"));
    }
  }

  async function handleOpenReportFromRun(reportId: string) {
    await handleSelectReport(reportId);
    navigateToPage("reports");
  }

  async function handleRetryAnalysisRun(analysisId: string) {
    setError(null);
    try {
      const status = await retryAnalysis(analysisId);
      setAnalysisStatus(status);
      await refreshAnalysisRuns();
      await refreshReports();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : t("errors.analysisRun"));
    }
  }

  async function loadReportComparison(reportId: string) {
    try {
      const comparison = await getReportComparison(reportId);
      setActiveReportComparison(comparison);
    } catch {
      setActiveReportComparison(null);
    }
  }

  const currentNavItem = navItems.find((item) => item.key === activePage);
  const latestSymbolReport = reports.find((report) => report.symbol === symbol.toUpperCase()) ?? null;

  return (
    <main className="min-h-screen bg-background text-foreground">
      <div className={cn("grid min-h-screen max-lg:grid-cols-1", sidebarCollapsed ? "grid-cols-[80px_minmax(0,1fr)]" : "grid-cols-[272px_minmax(0,1fr)]")}>
      <ShellSidebar
        title={t("title")}
        navItems={navItems}
        activePage={activePage}
        collapsed={sidebarCollapsed}
        onNavigate={(page) => {
          navigateToPage(page);
          setMobileNavOpen(false);
        }}
        onToggleCollapse={() => setSidebarCollapsed((collapsed) => !collapsed)}
      />
      {mobileNavOpen ? (
        <div className="fixed inset-0 z-40 bg-background/80 backdrop-blur lg:hidden">
          <div className="h-full w-[280px] border-r bg-sidebar shadow-lg">
            <ShellSidebar
              title={t("title")}
              navItems={navItems}
              activePage={activePage}
              collapsed={false}
              mobile
              onNavigate={(page) => {
                navigateToPage(page);
                setMobileNavOpen(false);
              }}
              onToggleCollapse={() => setMobileNavOpen(false)}
            />
          </div>
        </div>
      ) : null}

      <section className="min-w-0 bg-muted/20">
        <header className="sticky top-0 z-20 border-b bg-background/95 backdrop-blur">
          <div className="mx-auto flex max-w-[1480px] items-center justify-between gap-4 px-6 py-4 max-md:flex-col max-md:items-stretch max-sm:px-4">
            <div className="flex min-w-0 items-center gap-3">
              <Button type="button" variant="outline" size="icon" className="lg:hidden" onClick={() => setMobileNavOpen(true)} aria-label="Open navigation">
                <Menu />
              </Button>
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline">{t("productLine")}</Badge>
                </div>
                <h2 className="mt-1 truncate text-xl font-semibold tracking-normal">
                  {currentNavItem?.label ?? t("fallbackPageTitle")}
                </h2>
              </div>
            </div>
            <div className="flex min-w-0 items-end gap-3 max-xl:flex-wrap max-sm:flex-col max-sm:items-stretch">
              <SymbolSearch value={symbol} onChange={setSymbol} />
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={marketSession.status === "open" ? "default" : "secondary"} className="h-9 px-3">
                  {marketSession.label}
                </Badge>
                <Badge variant={optionsProviderReadiness?.ready ? "default" : "secondary"} className="h-9 px-3">
                  {optionsProviderReadiness?.ready ? t("readiness.polygonReady") : t("readiness.providerPending")}
                </Badge>
                <Button type="button" variant="outline" size="icon" onClick={toggleTheme} aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"} title={theme === "dark" ? "Light" : "Dark"}>
                  {theme === "dark" ? <Sun /> : <Moon />}
                </Button>
                <Button type="button" variant="outline" size="icon" onClick={toggleLanguage} aria-label="Switch language" title={i18n.language === "zh" ? "EN" : "中"}>
                  <Languages />
                </Button>
              </div>
            </div>
          </div>
        </header>

        <div className="mx-auto max-w-[1480px] px-6 py-6 max-sm:px-4">
        {activePage === "dashboard" ? (
          <DashboardPage
            symbol={symbol}
            reports={reports}
            analysisRuns={analysisRuns}
            bars={bars}
            marketPulseBars={marketPulseBars}
            optionSnapshots={optionSnapshots}
            optionContracts={optionContracts}
            syncSummary={syncSummary}
            readiness={optionsProviderReadiness}
            watchlist={watchlist}
            watchlistSaving={watchlistSaving}
            watchlistError={watchlistError}
            onSymbolChange={setSymbol}
            onSaveWatchlist={(symbols) => void saveResearchWatchlist(symbols)}
            onOpenReport={(reportId) => void handleOpenReportFromRun(reportId)}
            onNavigate={navigateToPage}
          />
        ) : null}

        {activePage === "analysis" ? (
          <div className="grid gap-4 xl:grid-cols-2">
            <div className="grid gap-4">
	              <AnalysisPanel
	                symbol={symbol}
	                supportedSymbols={SUPPORTED_SYMBOLS}
                loading={loading}
                error={error}
                status={analysisStatus}
                config={analysisConfig}
                onSymbolChange={setSymbol}
	                onConfigChange={setAnalysisConfig}
	                onRunAnalysis={handleRunAnalysis}
	              />
              <ResearchContextCard
                symbol={symbol}
                bars={bars}
                optionSnapshots={optionSnapshots}
                optionContracts={optionContracts}
                providerReadiness={providerReadiness}
                optionsProviderReadiness={optionsProviderReadiness}
                analysisConfig={analysisConfig}
                latestReport={reports[0] ?? null}
                onNavigate={navigateToPage}
              />
	              <RunsPreview runs={syncRuns} />
            </div>
            <ReportPanel report={activeReport} comparison={activeReportComparison} />
          </div>
        ) : null}

        {activePage === "reports" ? (
          <div className="grid gap-4 xl:grid-cols-2">
            <ReportHistory reports={reports} runs={analysisRuns} onSelectReport={handleSelectReport} />
            <ReportPanel report={activeReport} comparison={activeReportComparison} />
          </div>
        ) : null}

        {activePage === "market" ? (
          <div className="grid gap-4">
            <MarketDataControls
              symbol={symbol}
              timeframe={marketTimeframe}
              loading={marketLoading}
              error={marketError}
              bars={bars}
              onSymbolChange={setSymbol}
              onTimeframeChange={(timeframe) => void handleMarketTimeframeChange(timeframe)}
              onRefresh={() => void loadMarketContext(symbol, marketTimeframe)}
            />
            <Suspense fallback={<WorkbenchLoadingCard title={t("market.title")} />}>
              <KlineChart bars={bars} />
            </Suspense>
            <RecentBarsTable bars={bars} />
            <DataSyncPanel
              runs={syncRuns}
              summary={syncSummary}
              groups={syncGroups}
              health={syncHealth}
              readiness={providerReadiness}
              loading={syncLoading}
              syncing={syncing}
              error={syncError}
              providerFilter={syncProviderFilter}
              syncTypeFilter={syncTypeFilter}
              startedAfterFilter={syncStartedAfterFilter}
              startedBeforeFilter={syncStartedBeforeFilter}
              onProviderFilterChange={setSyncProviderFilter}
              onSyncTypeFilterChange={setSyncTypeFilter}
              onStartedAfterFilterChange={setSyncStartedAfterFilter}
              onStartedBeforeFilterChange={setSyncStartedBeforeFilter}
              onConfigureProvider={() => navigateToPage("settings")}
              onRefresh={() => void handleRefreshSyncRuns()}
              onSyncSample={() => void handleSyncSampleBars()}
            />
          </div>
        ) : null}

        {activePage === "options" ? (
          <div className="grid gap-4">
            <Suspense fallback={<WorkbenchLoadingCard title={t("options.title")} />}>
              <OptionChainTable
	                snapshots={optionSnapshots}
                contracts={optionContracts}
                contractsLoading={optionContractsLoading}
                contractsError={optionContractsError}
	                underlying={optionUnderlying}
                expiry={optionExpiry}
                loading={optionsLoading}
                syncing={optionsSyncing}
                error={optionsError}
                readiness={optionsProviderReadiness}
                syncHealth={optionsSyncHealth}
                latestSyncRun={latestOptionsSyncRun}
                selectedBars={selectedOptionBars}
                selectedBarsLoading={selectedOptionBarsLoading}
                selectedBarsError={selectedOptionBarsError}
                selectedBarsTimeframe={selectedOptionBarsTimeframe}
                onUnderlyingChange={handleOptionUnderlyingChange}
                onExpiryChange={handleOptionExpiryChange}
                onSelectedContractChange={(optionSymbol) => void loadSelectedOptionBars(optionSymbol)}
                onSelectedBarsTimeframeChange={(timeframe) => void handleSelectedOptionBarsTimeframeChange(timeframe)}
                onConfigureProvider={() => navigateToPage("settings")}
                onRefresh={() => void handleRefreshOptions()}
                onSync={() => void handleSyncOptions()}
              />
            </Suspense>
          </div>
        ) : null}

        {activePage === "strategy" ? (
          <StrategyLabPanel
            symbol={symbol}
            bars={bars}
            latestReport={latestSymbolReport}
            onRefreshMarket={() => void loadMarketContext(symbol, marketTimeframe)}
          />
        ) : null}

        {activePage === "runs" ? (
          <RunsPage
            analysisRuns={analysisRuns}
            runs={syncRuns}
            summary={syncSummary}
            groups={syncGroups}
            loading={syncLoading}
            error={syncError}
            onRefresh={() => void handleRefreshTaskCenter()}
            onOpenReport={(reportId) => void handleOpenReportFromRun(reportId)}
            onRetryAnalysis={(analysisId) => void handleRetryAnalysisRun(analysisId)}
          />
        ) : null}

        {activePage === "settings" ? (
          <SettingsPage
            readiness={providerReadiness}
            optionsReadiness={optionsProviderReadiness}
            health={syncHealth}
            optionsHealth={optionsSyncHealth}
            backendHealth={backendHealth}
            backendHealthError={backendHealthError}
            analysisConfig={analysisConfig}
            syncRuns={syncRuns}
            onRefresh={() => Promise.all([refreshBackendHealth(), refreshSyncRuns()]).then(() => undefined)}
          />
        ) : null}
        </div>
      </section>
      </div>
    </main>
  );
}

function toIsoDateTime(value: string) {
  return value ? new Date(value).toISOString() : undefined;
}

function inferAssetType(symbol: string): AnalysisStartPayload["assetType"] {
  if (symbol === "SPX" || symbol === "NDX" || symbol === "VIX") {
    return "index";
  }
  if (["SPY", "QQQ", "IWM", "DIA"].includes(symbol)) {
    return "etf";
  }
  if (/^\w+\d{6}[CP]\d+$/i.test(symbol)) {
    return "option";
  }
  return "equity";
}

function ShellSidebar({
  title,
  navItems,
  activePage,
  collapsed,
  mobile = false,
  onNavigate,
  onToggleCollapse,
}: {
  title: string;
  navItems: NavItem[];
  activePage: PageKey;
  collapsed: boolean;
  mobile?: boolean;
  onNavigate: (page: PageKey) => void;
  onToggleCollapse: () => void;
}) {
  return (
    <aside
      className={cn(
        "sticky top-0 flex h-screen flex-col border-r bg-sidebar text-sidebar-foreground max-lg:hidden",
        collapsed ? "px-3 py-4" : "px-4 py-4",
        mobile ? "!flex" : "",
      )}
    >
      <div className={cn("flex items-center gap-3", collapsed ? "justify-center" : "justify-between")}>
        <div className={cn("flex min-w-0 items-center gap-3", collapsed ? "hidden" : "")}>
          <div className="grid size-9 place-items-center rounded-lg bg-sidebar-primary text-sm font-semibold text-sidebar-primary-foreground">
            AQ
          </div>
          <div className="min-w-0">
            <h1 className="truncate text-lg font-semibold tracking-normal text-sidebar-foreground">{title}</h1>
          </div>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="shrink-0 text-muted-foreground"
          onClick={onToggleCollapse}
        >
          {mobile ? <X /> : collapsed ? <PanelLeftOpen /> : <PanelLeftClose />}
        </Button>
      </div>
      <Separator className="my-4" />
      <nav className="flex flex-1 flex-col gap-1">
        {navItems.map((item) => {
          const selected = activePage === item.key;
          const Icon = NAV_ICONS[item.key];
          return (
            <Button
              key={item.key}
              type="button"
              variant={selected ? "secondary" : "ghost"}
              className={cn(
                "h-auto w-full justify-start rounded-lg px-2.5 py-2.5 text-left",
                collapsed ? "justify-center px-0" : "gap-3",
              )}
              title={collapsed ? item.label : undefined}
              onClick={() => onNavigate(item.key)}
            >
              <Icon data-icon="inline-start" />
              {collapsed ? null : (
                <span className="flex min-w-0 flex-col items-start gap-0.5">
                  <span className="truncate text-sm font-medium leading-5">{item.label}</span>
                </span>
              )}
            </Button>
          );
        })}
      </nav>
    </aside>
  );
}

function SymbolSearch({ value, onChange }: { value: string; onChange: (symbol: string) => void }) {
  const normalizedValue = value.trim().toUpperCase();
  const suggestions = SUPPORTED_SYMBOLS.filter((symbol) => symbol.includes(normalizedValue || "SP")).slice(0, 5);

  return (
    <div className="flex min-w-[300px] flex-col gap-1 max-sm:min-w-0">
      <label className="flex flex-col gap-1">
        <span className="text-xs text-muted-foreground">Symbol</span>
        <Input className="w-72 font-semibold uppercase max-sm:w-full" value={value} onChange={(event) => onChange(event.target.value.toUpperCase())} />
      </label>
      <div className="flex flex-wrap gap-1">
        {(suggestions.length > 0 ? suggestions : SUPPORTED_SYMBOLS.slice(0, 5)).map((symbol) => (
          <Button
            key={symbol}
            type="button"
            variant={symbol === normalizedValue ? "secondary" : "outline"}
            size="sm"
            className="h-7 px-2 text-xs"
            onClick={() => onChange(symbol)}
          >
            {symbol}
          </Button>
        ))}
      </div>
    </div>
  );
}

function getMarketSessionState(t: (key: string) => string) {
  const now = new Date();
  const easternParts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    weekday: "short",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).formatToParts(now);
  const part = (type: string) => easternParts.find((item) => item.type === type)?.value ?? "";
  const weekday = part("weekday");
  const hour = Number(part("hour"));
  const minute = Number(part("minute"));
  const minutes = hour * 60 + minute;
  const isWeekday = !["Sat", "Sun"].includes(weekday);
  const open = 9 * 60 + 30;
  const close = 16 * 60;

  if (!isWeekday) {
    return { status: "closed", label: t("session.closed") };
  }
  if (minutes < open) {
    return { status: "pre", label: t("session.pre") };
  }
  if (minutes < close) {
    return { status: "open", label: t("session.open") };
  }
  return { status: "closed", label: t("session.after") };
}

function WorkbenchLoadingCard({ title }: { title: string }) {
  const { t } = useTranslation();
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{t("market.loading")}...</CardDescription>
      </CardHeader>
    </Card>
  );
}

function MarketDataControls({
  symbol,
  timeframe,
  loading,
  error,
  bars,
  onSymbolChange,
  onTimeframeChange,
  onRefresh,
}: {
  symbol: string;
  timeframe: MarketTimeframe;
  loading: boolean;
  error: string | null;
  bars: MarketBar[];
  onSymbolChange: (symbol: string) => void;
  onTimeframeChange: (timeframe: MarketTimeframe) => void;
  onRefresh: () => void;
}) {
  const { t } = useTranslation();
	  const latestBar = bars[0];
	  const latestClose = bars.length > 0 ? bars[bars.length - 1].close : null;
	  const indicators = calculateMarketIndicators(bars);
	  const regime = buildMarketRegime(bars, indicators);
	  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("market.title")}</CardTitle>
        <CardAction className="flex gap-2">
          <Button type="button" variant="outline" onClick={onRefresh} disabled={loading}>
            {loading ? t("market.loading") : t("market.refresh")}
          </Button>
        </CardAction>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {error ? (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}
        <div className="grid grid-cols-[minmax(180px,1fr)_180px] gap-3 max-sm:grid-cols-1">
          <label className="flex flex-col gap-2">
            <span className="text-sm text-muted-foreground">{t("market.symbol")}</span>
            <Input value={symbol} onChange={(event) => onSymbolChange(event.target.value.toUpperCase())} />
          </label>
          <label className="flex flex-col gap-2">
            <span className="text-sm text-muted-foreground">{t("market.timeframe")}</span>
            <Select value={timeframe} onValueChange={(value) => onTimeframeChange(value as MarketTimeframe)}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  <SelectItem value="1m">1m</SelectItem>
                  <SelectItem value="5m">5m</SelectItem>
                  <SelectItem value="1d">1d</SelectItem>
                </SelectGroup>
              </SelectContent>
            </Select>
          </label>
        </div>
        <div className="grid grid-cols-4 gap-3 max-lg:grid-cols-2 max-sm:grid-cols-1">
          <WorkbenchMetric label={t("market.bars")} value={bars.length.toLocaleString()} />
          <WorkbenchMetric label={t("market.latestClose")} value={latestClose === null ? "-" : latestClose.toFixed(2)} />
          <WorkbenchMetric label={t("market.source")} value={latestBar?.source ?? "-"} />
          <WorkbenchMetric label={t("market.timeframe")} value={timeframe} />
        </div>
	        <MarketIndicatorGrid indicators={indicators} />
	        <MarketRegimePanel regime={regime} />
      </CardContent>
    </Card>
  );
}

function RecentBarsTable({ bars }: { bars: MarketBar[] }) {
  const { t } = useTranslation();
  const recentBars = [...bars]
    .sort((left, right) => new Date(right.timestamp).getTime() - new Date(left.timestamp).getTime())
    .slice(0, 10);

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("market.recentBars")}</CardTitle>
      </CardHeader>
      <CardContent>
        {recentBars.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t("market.noBarsPreview")}</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Time</TableHead>
                <TableHead>Open</TableHead>
                <TableHead>High</TableHead>
                <TableHead>Low</TableHead>
                <TableHead>Close</TableHead>
                <TableHead>Volume</TableHead>
                <TableHead>Source</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {recentBars.map((bar) => (
                <TableRow key={`${bar.symbol}:${bar.timeframe}:${bar.timestamp}:${bar.source}`}>
                  <TableCell>{formatDate(bar.timestamp)}</TableCell>
                  <TableCell>{bar.open.toFixed(2)}</TableCell>
                  <TableCell>{bar.high.toFixed(2)}</TableCell>
                  <TableCell>{bar.low.toFixed(2)}</TableCell>
                  <TableCell>{bar.close.toFixed(2)}</TableCell>
                  <TableCell>{bar.volume.toLocaleString()}</TableCell>
                  <TableCell>{bar.source}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

function MarketPulseTile({ symbol, bars }: { symbol: string; bars: MarketBar[] }) {
  const { t } = useTranslation();
  const sortedBars = [...bars].sort((left, right) => new Date(left.timestamp).getTime() - new Date(right.timestamp).getTime());
  const latest = sortedBars[sortedBars.length - 1];
  const previous = sortedBars[sortedBars.length - 2];
  const change = latest && previous ? latest.close - previous.close : 0;
  const changePercent = latest && previous && previous.close !== 0 ? (change / previous.close) * 100 : 0;
  const tone = change > 0 ? "good" : change < 0 ? "bad" : undefined;

  return (
    <article className="flex min-h-36 flex-col justify-between rounded-lg border bg-card p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <strong>{symbol}</strong>
          <p className="text-xs text-muted-foreground">{latest?.source ?? "waiting"}</p>
        </div>
        <Badge variant={tone === "bad" ? "destructive" : "secondary"}>
          {latest ? `${changePercent >= 0 ? "+" : ""}${changePercent.toFixed(2)}%` : "-"}
        </Badge>
      </div>
      <MiniCandles bars={sortedBars} />
      <div className="flex items-end justify-between gap-3">
        <span className="text-xs text-muted-foreground">{latest ? formatDate(latest.timestamp) : t("market.noData")}</span>
        <strong className="text-lg">{latest ? latest.close.toFixed(2) : "-"}</strong>
      </div>
    </article>
  );
}

function MiniCandles({ bars }: { bars: MarketBar[] }) {
  const candles = miniCandleGeometry(bars);
  if (candles.length < 2) {
    return <div className="h-14 rounded-md bg-muted/50" aria-hidden="true" />;
  }
  return (
    <svg className="h-14 w-full rounded-md bg-muted/30" viewBox="0 0 160 56" role="img" aria-label="mini candlestick chart">
      {candles.map((candle) => {
        const color = candle.close >= candle.open ? MARKET_COLORS.up : MARKET_COLORS.down;
        return (
          <g key={candle.key}>
            <line x1={candle.x} x2={candle.x} y1={candle.highY} y2={candle.lowY} stroke={color} strokeWidth="1.4" />
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

function miniCandleGeometry(bars: MarketBar[]) {
  const source = bars.slice(-16);
  if (source.length < 2) return [];
  const lows = source.map((bar) => bar.low);
  const highs = source.map((bar) => bar.high);
  const min = Math.min(...lows);
  const max = Math.max(...highs);
  const spread = max - min || 1;
  const plotTop = 5;
  const plotHeight = 46;
  const step = 160 / source.length;
  const bodyWidth = Math.max(3, Math.min(7, step * 0.52));
  const y = (value: number) => plotTop + (1 - (value - min) / spread) * plotHeight;

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

function MarketIndicatorGrid({ indicators }: { indicators: MarketIndicators }) {
  return (
    <div className="grid grid-cols-6 gap-3 max-xl:grid-cols-3 max-md:grid-cols-2 max-sm:grid-cols-1">
      <WorkbenchMetric label="SMA20" value={formatIndicator(indicators.sma20)} />
      <WorkbenchMetric label="SMA50" value={formatIndicator(indicators.sma50)} />
      <WorkbenchMetric label="RSI14" value={formatIndicator(indicators.rsi14)} tone={rsiTone(indicators.rsi14)} />
      <WorkbenchMetric label="MACD" value={formatIndicator(indicators.macd)} tone={numberTone(indicators.macd)} />
      <WorkbenchMetric label="ATR14" value={formatIndicator(indicators.atr14)} />
      <WorkbenchMetric label="Vol MA20" value={formatVolumeIndicator(indicators.volumeMa20)} />
    </div>
  );
}

type MarketRegime = {
  trend: "bullish" | "bearish" | "neutral";
  momentum: "overbought" | "oversold" | "balanced" | "unknown";
  volatility: "high" | "normal" | "unknown";
  volume: "confirmed" | "quiet" | "unknown";
};

function MarketRegimePanel({ regime }: { regime: MarketRegime }) {
  const { t } = useTranslation();
  return (
    <div className="rounded-lg border bg-muted/30 p-3">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold">{t("market.regime.title")}</h3>
          <p className="mt-1 text-xs text-muted-foreground">{t("market.regime.description")}</p>
        </div>
        <Badge variant="secondary">SMA / RSI / ATR / Volume</Badge>
      </div>
      <div className="grid grid-cols-4 gap-2 max-lg:grid-cols-2 max-sm:grid-cols-1">
        <RegimeMetric label={t("market.regime.trend")} value={t(`market.regime.${regime.trend}`)} tone={regimeTone(regime.trend)} />
        <RegimeMetric label={t("market.regime.momentum")} value={t(`market.regime.${regime.momentum}`)} tone={regimeTone(regime.momentum)} />
        <RegimeMetric label={t("market.regime.volatility")} value={t(`market.regime.${regime.volatility}`)} tone={regimeTone(regime.volatility)} />
        <RegimeMetric label={t("market.regime.volume")} value={t(`market.regime.${regime.volume}`)} tone={regimeTone(regime.volume)} />
      </div>
    </div>
  );
}

function RegimeMetric({ label, value, tone }: { label: string; value: string; tone?: "good" | "warn" | "bad" }) {
  return (
    <div className="rounded-lg border bg-background p-3">
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs text-muted-foreground">{label}</p>
        {tone ? <span aria-hidden="true" className={cn("size-2.5 rounded-full", tone === "good" ? "bg-primary" : tone === "bad" ? "bg-destructive" : "bg-muted-foreground")} /> : null}
      </div>
      <p className="mt-1 truncate text-sm font-semibold">{value}</p>
    </div>
  );
}

function IndicatorPill({ label, value, tone }: { label: string; value: string; tone?: "good" | "warn" | "bad" }) {
  return (
    <div className="rounded-md border bg-background px-2.5 py-2">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div
        className={cn(
          "mt-1 text-sm font-semibold tabular-nums",
          tone === "good" ? "text-primary" : "",
          tone === "bad" ? "text-destructive" : "",
          tone === "warn" ? "text-muted-foreground" : "",
        )}
      >
        {value}
      </div>
    </div>
  );
}

type MarketIndicators = {
  sma20: number | null;
  sma50: number | null;
  rsi14: number | null;
  macd: number | null;
  macdSignal: number | null;
  atr14: number | null;
  volumeMa20: number | null;
};

function calculateMarketIndicators(bars: MarketBar[]): MarketIndicators {
  const sorted = [...bars].sort((left, right) => new Date(left.timestamp).getTime() - new Date(right.timestamp).getTime());
  const closes = sorted.map((bar) => bar.close);
  const volumes = sorted.map((bar) => bar.volume);
  const macdSeries = calculateMacdSeries(closes);

  return {
    sma20: simpleMovingAverage(closes, 20),
    sma50: simpleMovingAverage(closes, 50),
    rsi14: calculateRsi(closes, 14),
    macd: macdSeries.macd[macdSeries.macd.length - 1] ?? null,
    macdSignal: macdSeries.signal[macdSeries.signal.length - 1] ?? null,
    atr14: calculateAtr(sorted, 14),
    volumeMa20: simpleMovingAverage(volumes, 20),
  };
}

function buildMarketRegime(bars: MarketBar[], indicators: MarketIndicators): MarketRegime {
  const sorted = [...bars].sort((left, right) => new Date(left.timestamp).getTime() - new Date(right.timestamp).getTime());
  const latest = sorted[sorted.length - 1] ?? null;
  const trend =
    latest && indicators.sma20 !== null && indicators.sma50 !== null
      ? latest.close >= indicators.sma20 && indicators.sma20 >= indicators.sma50
        ? "bullish"
        : latest.close <= indicators.sma20 && indicators.sma20 <= indicators.sma50
          ? "bearish"
          : "neutral"
      : "neutral";
  const momentum =
    indicators.rsi14 === null
      ? "unknown"
      : indicators.rsi14 >= 70
        ? "overbought"
        : indicators.rsi14 <= 30
          ? "oversold"
          : "balanced";
  const volatility =
    latest && indicators.atr14 !== null
      ? indicators.atr14 / latest.close >= 0.025
        ? "high"
        : "normal"
      : "unknown";
  const volume =
    latest && indicators.volumeMa20 !== null
      ? latest.volume >= indicators.volumeMa20
        ? "confirmed"
        : "quiet"
      : "unknown";

  return { trend, momentum, volatility, volume };
}

function simpleMovingAverage(values: number[], period: number) {
  if (values.length < period) return null;
  const window = values.slice(-period);
  return window.reduce((sum, value) => sum + value, 0) / period;
}

function calculateRsi(closes: number[], period: number) {
  if (closes.length <= period) return null;
  const changes = closes.slice(1).map((close, index) => close - closes[index]);
  const window = changes.slice(-period);
  const gains = window.filter((change) => change > 0).reduce((sum, change) => sum + change, 0) / period;
  const losses = Math.abs(window.filter((change) => change < 0).reduce((sum, change) => sum + change, 0) / period);
  if (losses === 0) return 100;
  const rs = gains / losses;
  return 100 - 100 / (1 + rs);
}

function calculateMacdSeries(closes: number[]) {
  const ema12 = exponentialMovingAverageSeries(closes, 12);
  const ema26 = exponentialMovingAverageSeries(closes, 26);
  const macd = closes.map((_, index) => {
    const fast = ema12[index];
    const slow = ema26[index];
    return fast === null || slow === null ? null : fast - slow;
  });
  const signal = exponentialMovingAverageSeries(macd.filter((value): value is number => value !== null), 9);
  return {
    macd: macd.filter((value): value is number => value !== null),
    signal: signal.filter((value): value is number => value !== null),
  };
}

function exponentialMovingAverageSeries(values: number[], period: number) {
  const multiplier = 2 / (period + 1);
  let previous: number | null = null;
  return values.map((value, index) => {
    if (index + 1 < period) return null;
    if (previous === null) {
      previous = simpleMovingAverage(values.slice(0, index + 1), period);
      return previous;
    }
    previous = (value - previous) * multiplier + previous;
    return previous;
  });
}

function calculateAtr(bars: MarketBar[], period: number) {
  if (bars.length <= period) return null;
  const trueRanges = bars.slice(1).map((bar, index) => {
    const previousClose = bars[index].close;
    return Math.max(
      bar.high - bar.low,
      Math.abs(bar.high - previousClose),
      Math.abs(bar.low - previousClose),
    );
  });
  return simpleMovingAverage(trueRanges, period);
}

function formatIndicator(value: number | null) {
  return typeof value === "number" && Number.isFinite(value) ? value.toFixed(2) : "-";
}

function formatVolumeIndicator(value: number | null) {
  return typeof value === "number" && Number.isFinite(value) ? Math.round(value).toLocaleString() : "-";
}

function rsiTone(value: number | null): "good" | "warn" | "bad" | undefined {
  if (value === null) return undefined;
  if (value >= 70) return "bad";
  if (value <= 30) return "good";
  return "warn";
}

function numberTone(value: number | null): "good" | "bad" | undefined {
  if (value === null || value === 0) return undefined;
  return value > 0 ? "good" : "bad";
}

function regimeTone(value: MarketRegime[keyof MarketRegime]): "good" | "warn" | "bad" | undefined {
  if (["bullish", "oversold", "normal", "confirmed", "balanced"].includes(value)) return "good";
  if (["bearish", "overbought", "high"].includes(value)) return "bad";
  if (["neutral", "quiet"].includes(value)) return "warn";
  return undefined;
}

function buildOptionContractCoverage(contracts: OptionContract[]) {
  const strikes = contracts.map((contract) => contract.strike).filter((strike) => Number.isFinite(strike));
  const minStrike = strikes.length > 0 ? Math.min(...strikes) : null;
  const maxStrike = strikes.length > 0 ? Math.max(...strikes) : null;

  return {
    calls: contracts.filter((contract) => contract.option_type.toLowerCase() === "call").length,
    puts: contracts.filter((contract) => contract.option_type.toLowerCase() === "put").length,
    expiryCount: new Set(contracts.map((contract) => contract.expiry)).size,
    strikeRange: minStrike === null || maxStrike === null ? "-" : `${minStrike.toLocaleString()} - ${maxStrike.toLocaleString()}`,
  };
}

function DashboardPage({
  symbol,
  reports,
  analysisRuns,
  bars,
  marketPulseBars,
  optionSnapshots,
  optionContracts,
  syncSummary,
  readiness,
  watchlist,
  watchlistSaving,
  watchlistError,
  onSymbolChange,
  onSaveWatchlist,
  onOpenReport,
  onNavigate,
}: {
  symbol: string;
  reports: ReportListItem[];
  analysisRuns: AnalysisRunItem[];
  bars: MarketBar[];
  marketPulseBars: Record<string, MarketBar[]>;
  optionSnapshots: OptionSnapshot[];
  optionContracts: OptionContract[];
  syncSummary: ProviderSyncSummary | null;
  readiness: ProviderReadiness | null;
  watchlist: string[];
  watchlistSaving: boolean;
  watchlistError: string | null;
  onSymbolChange: (symbol: string) => void;
  onSaveWatchlist: (symbols: string[]) => void;
  onOpenReport: (reportId: string) => void;
  onNavigate: (page: PageKey) => void;
}) {
  const { t } = useTranslation();
  const latestReport = reports[0];
  const totalOptionVolume = optionSnapshots.reduce((sum, snapshot) => sum + snapshot.volume, 0);
  const optionContractCoverage = buildOptionContractCoverage(optionContracts);
	  const latestClose = bars.length > 0 ? bars[bars.length - 1].close : null;
	  const indicators = calculateMarketIndicators(bars);
  const normalizedSymbol = symbol.trim().toUpperCase();
  const canAddSymbol = SUPPORTED_SYMBOLS.includes(normalizedSymbol) && !watchlist.includes(normalizedSymbol);
	  const pipelineSteps = [
	    {
	      key: "provider",
	      label: t("dashboard.pipeline.provider"),
	      detail: readiness?.ready ? t("dashboard.pipeline.ready") : t("dashboard.pipeline.configureProvider"),
	      ready: Boolean(readiness?.ready),
	      page: "settings" as PageKey,
	    },
	    {
	      key: "bars",
	      label: t("dashboard.pipeline.bars"),
	      detail: bars.length ? t("dashboard.pipeline.barsReady", { count: bars.length }) : t("dashboard.pipeline.barsPending"),
	      ready: bars.length > 0,
	      page: "market" as PageKey,
	    },
	    {
	      key: "options",
	      label: t("dashboard.pipeline.options"),
	      detail: optionSnapshots.length ? t("dashboard.pipeline.optionsReady", { count: optionSnapshots.length }) : t("dashboard.pipeline.optionsPending"),
	      ready: optionSnapshots.length > 0,
	      page: "options" as PageKey,
	    },
	    {
	      key: "analysis",
	      label: t("dashboard.pipeline.analysis"),
	      detail: analysisRuns.length ? t("dashboard.pipeline.analysisReady", { count: analysisRuns.length }) : t("dashboard.pipeline.analysisPending"),
	      ready: analysisRuns.length > 0,
	      page: "analysis" as PageKey,
	    },
	    {
	      key: "report",
	      label: t("dashboard.pipeline.report"),
	      detail: reports.length ? t("dashboard.pipeline.reportReady", { count: reports.length }) : t("dashboard.pipeline.reportPending"),
	      ready: reports.length > 0,
	      page: "reports" as PageKey,
	    },
	  ];
	  const researchQueue = analysisRuns
    .filter((run) => ["running", "failed"].includes(normalizeRunStatus(run.status)))
    .slice(0, 4);
  return (
	    <div className="grid gap-4">
	      <Card>
	        <CardHeader>
	          <CardTitle>{t("dashboard.pipeline.title")}</CardTitle>
	        </CardHeader>
	        <CardContent className="grid grid-cols-5 gap-3 max-xl:grid-cols-3 max-md:grid-cols-2 max-sm:grid-cols-1">
	          {pipelineSteps.map((step, index) => (
	            <Button
	              key={step.key}
	              type="button"
	              variant={step.ready ? "secondary" : "outline"}
	              className="h-auto justify-start p-3 text-left"
	              onClick={() => onNavigate(step.page)}
	            >
	              <span className="flex size-7 shrink-0 items-center justify-center rounded-lg border bg-background text-xs font-semibold">
	                {index + 1}
	              </span>
	              <span className="flex min-w-0 flex-col items-start gap-1">
	                <span className="truncate text-sm font-semibold">{step.label}</span>
	                <span className="line-clamp-2 text-xs text-muted-foreground">{step.detail}</span>
	              </span>
	            </Button>
	          ))}
	        </CardContent>
	      </Card>

	      <Card>
        <CardHeader>
          <div className="flex min-w-0 flex-col gap-2">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="secondary">{symbol}</Badge>
              <Badge variant="outline">{t("dashboard.watchlistCount", { count: watchlist.length })}</Badge>
              {watchlistSaving ? <Badge variant="outline">{t("dashboard.savingWatchlist")}</Badge> : null}
            </div>
            <CardTitle>{t("dashboard.promptTitle")}</CardTitle>
          </div>
          <CardAction className="flex flex-wrap gap-2">
            <Button type="button" onClick={() => onNavigate("analysis")}>
              {t("dashboard.researchSymbol", { symbol })}
            </Button>
            <Button type="button" variant="outline" onClick={() => onNavigate("options")}>
              {t("dashboard.viewOptions")}
            </Button>
          </CardAction>
        </CardHeader>
        <CardContent className="grid grid-cols-[minmax(0,1fr)_320px] gap-4 max-xl:grid-cols-1">
          <div className="grid gap-3">
            {watchlistError ? (
              <Alert variant="destructive">
                <AlertDescription>{watchlistError}</AlertDescription>
              </Alert>
            ) : null}
            <div className="grid grid-cols-3 gap-2 max-lg:grid-cols-2 max-sm:grid-cols-1">
              {watchlist.map((candidate) => (
                <div key={candidate} className="grid grid-cols-[minmax(0,1fr)_40px] gap-2">
                  <Button
                    type="button"
                    variant={candidate === symbol ? "secondary" : "outline"}
                    className="justify-between"
                    onClick={() => onSymbolChange(candidate)}
                  >
                    <span>{candidate}</span>
                    {candidate === symbol ? <Badge variant="outline">active</Badge> : null}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    disabled={watchlistSaving || watchlist.length <= 1}
                    aria-label={t("dashboard.removeFromWatchlist", { symbol: candidate })}
                    title={t("dashboard.removeFromWatchlist", { symbol: candidate })}
                    onClick={() => onSaveWatchlist(watchlist.filter((item) => item !== candidate))}
                  >
                    <X />
                  </Button>
                </div>
              ))}
            </div>
            {canAddSymbol ? (
              <Button
                type="button"
                variant="outline"
                className="justify-start"
                disabled={watchlistSaving}
                onClick={() => onSaveWatchlist([...watchlist, normalizedSymbol])}
              >
                {t("dashboard.addToWatchlist", { symbol: normalizedSymbol })}
              </Button>
            ) : null}
          </div>
          <div className="grid gap-3 rounded-lg border bg-muted/30 p-3">
            <div className="flex items-center justify-between gap-3">
              <span className="text-sm text-muted-foreground">{t("market.latestClose")}</span>
              <strong className="text-lg">{latestClose === null ? "-" : latestClose.toFixed(2)}</strong>
            </div>
            <Separator />
            <div className="grid grid-cols-2 gap-2">
              <IndicatorPill label="SMA20" value={formatIndicator(indicators.sma20)} />
              <IndicatorPill label="SMA50" value={formatIndicator(indicators.sma50)} />
              <IndicatorPill label="RSI14" value={formatIndicator(indicators.rsi14)} tone={rsiTone(indicators.rsi14)} />
              <IndicatorPill label="MACD" value={formatIndicator(indicators.macd)} tone={numberTone(indicators.macd)} />
              <IndicatorPill label="ATR14" value={formatIndicator(indicators.atr14)} />
              <IndicatorPill label="Vol MA20" value={formatVolumeIndicator(indicators.volumeMa20)} />
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-[minmax(0,1.35fr)_minmax(360px,0.65fr)] gap-4 max-2xl:grid-cols-1">
        <Card>
          <CardHeader>
            <CardTitle>{t("dashboard.marketPulse")}</CardTitle>
            <CardAction>
              <Button type="button" variant="outline" onClick={() => onNavigate("market")}>
                {t("dashboard.openMarket")}
              </Button>
            </CardAction>
          </CardHeader>
          <CardContent className="grid grid-cols-4 gap-3 max-xl:grid-cols-2 max-sm:grid-cols-1">
            {MARKET_PULSE_SYMBOLS.map((pulseSymbol) => (
              <MarketPulseTile key={pulseSymbol} symbol={pulseSymbol} bars={marketPulseBars[pulseSymbol] ?? []} />
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("dashboard.researchQueue")}</CardTitle>
            <CardAction>
              <Button type="button" variant="outline" onClick={() => onNavigate("runs")}>
                {t("dashboard.taskCenter")}
              </Button>
            </CardAction>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {researchQueue.length > 0 ? (
              researchQueue.map((run) => (
                <article key={run.analysis_id} className="rounded-lg border bg-card p-3">
                  <div className="flex items-center justify-between gap-3">
                    <strong>{run.symbol}</strong>
                    <Badge variant={normalizeRunStatus(run.status) === "failed" ? "destructive" : "secondary"}>{run.status}</Badge>
                  </div>
                  <p className="mt-2 truncate text-sm text-muted-foreground">
                    {run.llm_provider} · {run.model} · {run.depth}
                  </p>
                </article>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">{t("dashboard.noResearchQueue")}</p>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-2 gap-4 max-xl:grid-cols-1">
        <Card>
          <CardHeader>
            <CardTitle>{t("dashboard.aiFindings")}</CardTitle>
            <CardAction>
              <Button type="button" variant="outline" onClick={() => onNavigate("reports")}>
                {t("dashboard.openReports")}
              </Button>
            </CardAction>
          </CardHeader>
          <CardContent>
            {latestReport ? (
              <article className="grid gap-3">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="secondary">{latestReport.symbol}</Badge>
                  <Badge variant="outline">{t("dashboard.confidence", { value: (latestReport.confidence * 100).toFixed(0) })}</Badge>
                  <Badge variant="outline">{latestReport.analyst_set}</Badge>
                </div>
                <p className="text-sm leading-6 text-muted-foreground">{latestReport.summary}</p>
                <div className="flex flex-wrap gap-2">
                  <Button type="button" size="sm" onClick={() => onOpenReport(latestReport.report_id)}>
                    <FileText data-icon="inline-start" />
                    {t("dashboard.openLatestReport")}
                  </Button>
                  <Button type="button" variant="outline" size="sm" onClick={() => onNavigate("analysis")}>
                    <Bot data-icon="inline-start" />
                    {t("dashboard.startFollowUp")}
                  </Button>
                </div>
              </article>
            ) : (
              <p className="text-sm text-muted-foreground">{t("dashboard.noReport")}</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>{t("dashboard.optionsWatch")}</CardTitle>
            <CardAction>
              <Button type="button" variant="outline" onClick={() => onNavigate("options")}>
                {t("dashboard.viewOptions")}
              </Button>
            </CardAction>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-3 max-sm:grid-cols-1">
            <WorkbenchMetric label={t("dashboard.optionSnapshots")} value={optionSnapshots.length.toLocaleString()} />
            <WorkbenchMetric label={t("dashboard.optionContracts")} value={optionContracts.length.toLocaleString()} />
            <WorkbenchMetric label={t("dashboard.optionVolume")} value={totalOptionVolume.toLocaleString()} />
            <WorkbenchMetric label={t("dashboard.optionExpiries")} value={optionContractCoverage.expiryCount.toLocaleString()} />
            <WorkbenchMetric label={t("dashboard.callPutCoverage")} value={`${optionContractCoverage.calls.toLocaleString()} / ${optionContractCoverage.puts.toLocaleString()}`} />
            <WorkbenchMetric label={t("dashboard.strikeRange")} value={optionContractCoverage.strikeRange} />
            {syncSummary ? (
              <>
                <WorkbenchMetric label={t("dashboard.syncRuns")} value={syncSummary.total_runs.toLocaleString()} />
                <WorkbenchMetric label={t("dashboard.failed")} value={syncSummary.failed.toLocaleString()} tone={syncSummary.failed > 0 ? "bad" : "good"} />
              </>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function RunsPage({
  analysisRuns,
  runs,
  summary,
  groups,
  loading,
  error,
  onRefresh,
  onOpenReport,
  onRetryAnalysis,
}: {
  analysisRuns: AnalysisRunItem[];
  runs: ProviderSyncRunItem[];
  summary: ProviderSyncSummary | null;
  groups: ProviderSyncSummaryGroup[];
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
  onOpenReport: (reportId: string) => void;
  onRetryAnalysis: (analysisId: string) => void;
}) {
  const { t } = useTranslation();
  const [analysisStatusFilter, setAnalysisStatusFilter] = useState("all");
  const [selectedRunStatus, setSelectedRunStatus] = useState<AnalysisStatus | null>(null);
  const [selectedRunLoading, setSelectedRunLoading] = useState(false);
  const [selectedRunError, setSelectedRunError] = useState<string | null>(null);
  const filteredAnalysisRuns = useMemo(
    () =>
      analysisStatusFilter === "all"
        ? analysisRuns
        : analysisRuns.filter((run) => normalizeRunStatus(run.status) === analysisStatusFilter),
    [analysisRuns, analysisStatusFilter],
  );
	  const completedRuns = analysisRuns.filter((run) => normalizeRunStatus(run.status) === "completed").length;
	  const failedRuns = analysisRuns.filter((run) => normalizeRunStatus(run.status) === "failed").length;
	  const runningRuns = analysisRuns.filter((run) => normalizeRunStatus(run.status) === "running").length;
	  const latestAnalysisRun = analysisRuns[0] ?? null;
	  const latestProviderRun = runs[0] ?? null;

  async function handleInspectRun(run: AnalysisRunItem) {
    setSelectedRunLoading(true);
    setSelectedRunError(null);
    try {
      const status = await getAnalysisStatus(run.analysis_id);
      setSelectedRunStatus(status);
    } catch (caught) {
      setSelectedRunStatus(null);
      setSelectedRunError(caught instanceof Error ? caught.message : t("runs.detailError"));
    } finally {
      setSelectedRunLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <Card>
      <CardHeader>
          <CardTitle>{t("runs.title")}</CardTitle>
          <CardAction>
          <Button type="button" variant="outline" onClick={onRefresh} disabled={loading}>
            {loading ? t("runs.refreshing") : t("runs.refresh")}
          </Button>
          </CardAction>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
	        {error ? (
	          <Alert variant="destructive">
	            <AlertDescription>{error}</AlertDescription>
	          </Alert>
	        ) : null}
        <RunOperationsStrip
          latestAnalysisRun={latestAnalysisRun}
          latestProviderRun={latestProviderRun}
          summary={summary}
          runningRuns={runningRuns}
          failedRuns={failedRuns}
        />
	        <div className="grid grid-cols-4 gap-3 max-lg:grid-cols-2 max-sm:grid-cols-1">
          <WorkbenchMetric label={t("runs.analysisRuns")} value={analysisRuns.length.toLocaleString()} />
          <WorkbenchMetric label={t("runs.running")} value={runningRuns.toLocaleString()} tone={runningRuns > 0 ? "warn" : undefined} />
          <WorkbenchMetric label={t("runs.completed")} value={completedRuns.toLocaleString()} tone="good" />
          <WorkbenchMetric label={t("runs.failed")} value={failedRuns.toLocaleString()} tone={failedRuns > 0 ? "bad" : "good"} />
        </div>
        <Tabs value={analysisStatusFilter} onValueChange={setAnalysisStatusFilter}>
          <TabsList className="w-fit">
            <TabsTrigger value="all">{t("runs.all")}</TabsTrigger>
            <TabsTrigger value="running">{t("runs.running")}</TabsTrigger>
            <TabsTrigger value="completed">{t("runs.completed")}</TabsTrigger>
            <TabsTrigger value="failed">{t("runs.failed")}</TabsTrigger>
          </TabsList>
        </Tabs>
        <AnalysisRunTable
          runs={filteredAnalysisRuns}
          onOpenReport={onOpenReport}
          onRetryAnalysis={onRetryAnalysis}
          onInspectRun={(run) => void handleInspectRun(run)}
        />
        <AnalysisRunDetailPanel status={selectedRunStatus} loading={selectedRunLoading} error={selectedRunError} />
        <Separator />
        {summary ? (
          <div className="grid grid-cols-5 gap-3 max-lg:grid-cols-2 max-sm:grid-cols-1">
            <WorkbenchMetric label={t("runs.totalRuns")} value={summary.total_runs.toLocaleString()} />
            <WorkbenchMetric label={t("runs.succeeded")} value={summary.succeeded.toLocaleString()} tone="good" />
            <WorkbenchMetric label={t("runs.failed")} value={summary.failed.toLocaleString()} tone={summary.failed > 0 ? "bad" : "good"} />
            <WorkbenchMetric label={t("runs.rowsWritten")} value={summary.rows_written.toLocaleString()} />
            <WorkbenchMetric label={t("runs.averageDuration")} value={`${summary.average_duration_ms} ms`} />
          </div>
        ) : null}
        <SyncRunTable runs={runs} />
        </CardContent>
      </Card>

      {groups.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>{t("runs.providerGroups")}</CardTitle>
          </CardHeader>
          <CardContent>
          <div className="flex flex-col gap-2">
            {groups.map((group) => (
              <article key={`${group.provider}:${group.sync_type}`} className="flex flex-wrap items-center justify-between gap-3 rounded-lg border p-3">
                <div className="flex items-center gap-2">
                  <strong>{group.provider}</strong>
                  <Badge variant="secondary">{group.sync_type}</Badge>
                </div>
                <div className="flex flex-wrap gap-3 text-sm text-muted-foreground">
                  <span>{group.succeeded}/{group.total_runs} {t("runs.succeeded")}</span>
                  <span>{group.failed} {t("runs.failed")}</span>
                  <span>{group.rows_written.toLocaleString()} rows</span>
                </div>
              </article>
            ))}
          </div>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

function SettingsPage({
  readiness,
  optionsReadiness,
  health,
  optionsHealth,
  backendHealth,
  backendHealthError,
  analysisConfig,
  syncRuns,
  onRefresh,
}: {
  readiness: ProviderReadiness | null;
  optionsReadiness: ProviderReadiness | null;
  health: ProviderSyncHealth | null;
  optionsHealth: ProviderSyncHealth | null;
  backendHealth: BackendHealth | null;
  backendHealthError: string | null;
  analysisConfig: Pick<AnalysisStartPayload, "analysisDate" | "llmProvider" | "model" | "depth" | "analystSet" | "researchTemplate">;
  syncRuns: ProviderSyncRunItem[];
  onRefresh: () => void | Promise<void>;
}) {
  const { t } = useTranslation();
  const recentRuns = syncRuns.slice(0, 4);
  const catalog = getSettingsCatalog();
  const [settingValues, setSettingValues] = useState<Record<string, string>>({});
  const [secretValues, setSecretValues] = useState<Record<string, string>>({});
  const [persistedSettings, setPersistedSettings] = useState<Record<string, SettingItem>>({});
  const [dirtyKeys, setDirtyKeys] = useState<string[]>([]);
  const [settingsLoading, setSettingsLoading] = useState(false);
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [settingsError, setSettingsError] = useState<string | null>(null);
  const [settingsSavedAt, setSettingsSavedAt] = useState<string | null>(null);
  const [settingsSaveNotice, setSettingsSaveNotice] = useState(false);
  const settingsTabs = [
    { value: "apis", title: t("settings.tabs.apis"), detail: t("settings.nav.apis"), icon: KeyRound, sections: catalog.apiSections },
    { value: "models", title: t("settings.tabs.models"), detail: t("settings.nav.models"), icon: Bot, sections: catalog.modelSections },
    { value: "data", title: t("settings.tabs.data"), detail: t("settings.nav.data"), icon: Workflow, sections: catalog.dataSections },
    { value: "user", title: t("settings.tabs.user"), detail: t("settings.nav.user"), icon: SlidersHorizontal, sections: catalog.userSections },
    { value: "system", title: t("settings.tabs.system"), detail: t("settings.nav.system"), icon: ShieldCheck, sections: catalog.systemSections },
    { value: "health", title: t("settings.tabs.health"), detail: t("settings.nav.health"), icon: Activity, sections: [] },
  ] as const;
  const allSettingSections = [
    ...catalog.apiSections,
    ...catalog.modelSections,
    ...catalog.dataSections,
    ...catalog.userSections,
    ...catalog.systemSections,
  ];
  const settingEntryCount = allSettingSections.reduce((count, section) => count + section.items.length, 0);
  const secretSettingCount = allSettingSections
    .flatMap((section) => section.items)
    .flatMap((item) => item.configKeys)
    .filter((configKey) => isSecretConfigKey(configKey)).length;
  const savedSecretCount = Object.values(persistedSettings).filter((item) => item.is_secret && item.has_value).length;
  useEffect(() => {
    void loadPersistedSettings();
  }, []);

  async function loadPersistedSettings() {
    setSettingsLoading(true);
    setSettingsError(null);
    try {
      const response = await listSettings();
      applyPersistedSettings(response.items);
    } catch (caught) {
      setSettingsError(caught instanceof Error ? caught.message : t("settings.loadError"));
    } finally {
      setSettingsLoading(false);
    }
  }

  function applyPersistedSettings(items: SettingItem[]) {
    setPersistedSettings(Object.fromEntries(items.map((item) => [item.key, item])));
    setSettingValues(
      Object.fromEntries(
        items.filter((item) => !item.is_secret && item.value !== null).map((item) => [item.key, item.value ?? ""]),
      ),
    );
    setSettingsSavedAt(items[0]?.updated_at ?? null);
  }

  function handleSettingValueChange(configKey: string, value: string) {
    if (isSecretConfigKey(configKey)) {
      setSecretValues((current) => ({ ...current, [configKey]: value }));
    } else {
      setSettingValues((current) => ({ ...current, [configKey]: value }));
    }
    setSettingsSaveNotice(false);
    setDirtyKeys((current) => (current.includes(configKey) ? current : [...current, configKey]));
  }

  async function handleSaveSettings(configKeys?: string[]) {
    const targetKeys = configKeys ? dirtyKeys.filter((key) => configKeys.includes(key)) : dirtyKeys;
    const items = targetKeys
      .map((configKey) => {
        const secret = isSecretConfigKey(configKey);
        const value = secret ? secretValues[configKey] ?? "" : settingValues[configKey] ?? defaultConfigValue(configKey);
        if (secret && !value) return null;
        return {
          key: configKey,
          value,
          category: settingCategory(configKey, catalog),
          is_secret: secret,
        };
      })
      .filter((item): item is NonNullable<typeof item> => item !== null);

    if (items.length === 0) return;
    setSettingsSaving(true);
    setSettingsError(null);
    try {
      const response = await upsertSettings(items);
      applyPersistedSettings(response.items);
      setSecretValues({});
      setDirtyKeys([]);
      await onRefresh();
      setSettingsSaveNotice(true);
    } catch (caught) {
      setSettingsError(caught instanceof Error ? caught.message : t("settings.saveError"));
    } finally {
      setSettingsSaving(false);
    }
  }

  function handleResetSettingsForm() {
    applyPersistedSettings(Object.values(persistedSettings));
    setSecretValues({});
    setDirtyKeys([]);
    setSettingsSaveNotice(false);
  }

  return (
    <Tabs defaultValue="apis" orientation="vertical" className="grid gap-5">
      <div className="flex items-start justify-between gap-4 max-lg:flex-col">
        <div className="max-w-4xl">
          <div className="flex flex-wrap items-center gap-3">
            <h2 className="text-3xl font-semibold tracking-normal">{t("settings.title")}</h2>
            <Badge variant="secondary">{t("settings.editable")}</Badge>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2 sm:flex sm:flex-wrap">
          <Button type="button" variant="outline" onClick={handleResetSettingsForm} disabled={settingsSaving || dirtyKeys.length === 0}>
            {t("settings.reset")}
          </Button>
          <Button type="button" onClick={() => void handleSaveSettings()} disabled={settingsSaving || dirtyKeys.length === 0}>
            {settingsSaving ? t("settings.saving") : t("settings.save")}
          </Button>
        </div>
      </div>

      <section className="grid grid-cols-4 gap-3 max-xl:grid-cols-2 max-sm:grid-cols-1">
        <StatusCard label={t("settings.overview.saveStatus")} value={dirtyKeys.length > 0 ? t("settings.overview.unsaved") : t("settings.overview.synced")} detail={dirtyKeys.length > 0 ? t("settings.overview.unsavedDetail", { count: dirtyKeys.length }) : t("settings.overview.syncedDetail")} status={dirtyKeys.length > 0 ? "warn" : "good"} />
        <StatusCard label={t("settings.overview.defaultProvider")} value={readiness?.provider ?? "polygon"} detail={readiness?.ready ? t("settings.ready") : t("settings.notReady")} status={readiness?.ready ? "good" : "warn"} />
        <StatusCard label={t("settings.overview.lastSaved")} value={settingsSavedAt ? formatDate(settingsSavedAt) : t("settings.overview.neverSaved")} detail={settingsSavedAt ? t("settings.overview.reloadSafe") : t("settings.notSaved")} status={settingsSavedAt ? "good" : "warn"} />
        <StatusCard label={t("settings.overview.secretKeys")} value={`${savedSecretCount}/${secretSettingCount}`} detail={t("settings.secretWriteOnly")} status={savedSecretCount > 0 ? "good" : "warn"} />
      </section>

      {settingsError ? (
        <Alert variant="destructive">
          <AlertDescription>{settingsError}</AlertDescription>
        </Alert>
      ) : null}
      {!settingsError && settingsSaveNotice && settingsSavedAt ? (
        <Alert>
          <AlertDescription>{t("settings.savedAndRefreshed", { time: formatDate(settingsSavedAt) })}</AlertDescription>
        </Alert>
      ) : null}
      {backendHealthError ? (
        <Alert variant="destructive">
          <AlertDescription>{backendHealthError}</AlertDescription>
        </Alert>
      ) : null}

      <div className="grid gap-5 xl:grid-cols-[360px_minmax(0,1fr)]">
        <aside className="grid gap-4 xl:sticky xl:top-24 xl:h-fit">
          <Card>
            <CardContent className="pt-0">
              <TabsList className="grid h-auto w-full grid-cols-2 gap-2 bg-transparent p-0 max-sm:grid-cols-1 xl:grid-cols-1">
                {settingsTabs.map((item) => {
                  const Icon = item.icon;
                  const count = item.value === "health" ? 4 : item.sections.reduce((total, section) => total + section.items.length, 0);
                  return (
                    <TabsTrigger
                      key={item.value}
                      value={item.value}
                      className="grid h-auto min-h-16 grid-cols-[44px_minmax(0,1fr)_auto] items-center gap-3 rounded-lg border bg-background p-3 text-left data-active:border-foreground/20 data-active:bg-muted"
                    >
                      <span className="grid size-10 place-items-center rounded-md border bg-card text-muted-foreground">
                        <Icon className="size-4" />
                      </span>
                      <span className="min-w-0">
                        <span className="block text-sm font-semibold text-foreground">{item.title}</span>
                        <span className="mt-1 block truncate text-xs font-normal text-muted-foreground">{item.detail}</span>
                      </span>
                      <Badge variant="secondary">{count}</Badge>
                    </TabsTrigger>
                  );
                })}
              </TabsList>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="grid gap-3 pt-0">
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm font-medium">{t("settings.summary.settingEntries")}</span>
                <Badge variant="secondary">{settingEntryCount}</Badge>
              </div>
              <div className="grid gap-2">
                <Button type="button" variant="outline" onClick={() => void Promise.all([onRefresh(), loadPersistedSettings()])} disabled={settingsLoading}>
                  {settingsLoading ? t("settings.loading") : t("settings.refresh")}
                </Button>
              </div>
            </CardContent>
          </Card>
        </aside>

        <div className="min-w-0">
          <TabsContent value="apis" className="grid gap-4">
            {catalog.apiSections.map((section) => (
              <SettingsCatalogCard key={section.id} section={section} kind="api" readiness={readiness} optionsReadiness={optionsReadiness} settingValues={settingValues} secretValues={secretValues} persistedSettings={persistedSettings} dirtyKeys={dirtyKeys} saving={settingsSaving} onValueChange={handleSettingValueChange} onSaveSection={(keys) => void handleSaveSettings(keys)} />
            ))}
          </TabsContent>

          <TabsContent value="models" className="grid gap-4">
            {catalog.modelSections.map((section) => (
              <SettingsCatalogCard key={section.id} section={section} kind="model" readiness={readiness} optionsReadiness={optionsReadiness} settingValues={settingValues} secretValues={secretValues} persistedSettings={persistedSettings} dirtyKeys={dirtyKeys} saving={settingsSaving} onValueChange={handleSettingValueChange} onSaveSection={(keys) => void handleSaveSettings(keys)} />
            ))}
          </TabsContent>

          <TabsContent value="data" className="grid gap-4">
            {catalog.dataSections.map((section) => (
              <SettingsCatalogCard key={section.id} section={section} kind="data" readiness={readiness} optionsReadiness={optionsReadiness} settingValues={settingValues} secretValues={secretValues} persistedSettings={persistedSettings} dirtyKeys={dirtyKeys} saving={settingsSaving} onValueChange={handleSettingValueChange} onSaveSection={(keys) => void handleSaveSettings(keys)} />
            ))}
          </TabsContent>

          <TabsContent value="user" className="grid gap-4">
            <Card>
              <CardHeader>
                <CardTitle>{t("settings.modelDefaults")}</CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-4 gap-3 max-xl:grid-cols-2 max-sm:grid-cols-1">
                <WorkbenchMetric label="Provider" value={analysisConfig.llmProvider} />
                <WorkbenchMetric label="Model" value={analysisConfig.model} />
                <WorkbenchMetric label="Depth" value={analysisConfig.depth} />
                <WorkbenchMetric label="Analyst Set" value={analysisConfig.analystSet} />
              </CardContent>
            </Card>
            {catalog.userSections.map((section) => (
              <SettingsCatalogCard key={section.id} section={section} kind="user" settingValues={settingValues} secretValues={secretValues} persistedSettings={persistedSettings} dirtyKeys={dirtyKeys} saving={settingsSaving} onValueChange={handleSettingValueChange} onSaveSection={(keys) => void handleSaveSettings(keys)} />
            ))}
          </TabsContent>

          <TabsContent value="system" className="grid gap-4">
            {catalog.systemSections.map((section) => (
              <SettingsCatalogCard key={section.id} section={section} kind="system" settingValues={settingValues} secretValues={secretValues} persistedSettings={persistedSettings} dirtyKeys={dirtyKeys} saving={settingsSaving} onValueChange={handleSettingValueChange} onSaveSection={(keys) => void handleSaveSettings(keys)} />
            ))}
          </TabsContent>

          <TabsContent value="health" className="grid grid-cols-2 gap-4 max-xl:grid-cols-1">
          <Card>
            <CardHeader>
              <CardTitle>{t("settings.preflight.title")}</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3">
              <PreflightRow label={t("settings.preflight.backend")} ready={backendHealth?.status === "ok"} detail={backendHealth?.status ?? t("settings.noRecord")} />
              <PreflightRow label={t("settings.preflight.market")} ready={Boolean(readiness?.ready)} detail={readiness?.ready ? t("settings.ready") : readiness?.missing?.join(", ") || t("settings.notReady")} />
              <PreflightRow label={t("settings.preflight.options")} ready={Boolean(optionsReadiness?.ready)} detail={optionsReadiness?.ready ? t("settings.ready") : optionsReadiness?.missing?.join(", ") || t("settings.notReady")} />
              <PreflightRow label={t("settings.preflight.database")} ready={Boolean(settingsSavedAt)} detail={settingsSavedAt ? formatDate(settingsSavedAt) : t("settings.notSaved")} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t("settings.dataHealth")}</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              <StatusRow label={t("settings.barsSync")} value={health ? healthStatusLabel(health.status, t) : t("settings.noRecord")} status={health?.status ?? "missing"} detail={health?.message ?? t("settings.barsWaiting")} />
              <StatusRow label={t("settings.optionsSync")} value={optionsHealth ? healthStatusLabel(optionsHealth.status, t) : t("settings.noRecord")} status={optionsHealth?.status ?? "missing"} detail={optionsHealth?.message ?? t("settings.optionsWaiting")} />
              <p className="text-xs text-muted-foreground">{t("settings.secretNote")}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{t("settings.recentSync")}</CardTitle>
            </CardHeader>
            <CardContent>
              {recentRuns.length > 0 ? <SyncRunTable runs={recentRuns} compact /> : <p className="text-sm text-muted-foreground">{t("settings.noSyncRuns")}</p>}
            </CardContent>
          </Card>
        </TabsContent>
      </div>
      </div>
    </Tabs>
  );
}

function SettingsCatalogCard({
  section,
  kind,
  readiness,
  optionsReadiness,
  settingValues,
  secretValues,
  persistedSettings,
  dirtyKeys,
  saving,
  onValueChange,
  onSaveSection,
}: {
  section: SettingsCatalogSection;
  kind: "api" | "model" | "data" | "user" | "system";
  readiness?: ProviderReadiness | null;
  optionsReadiness?: ProviderReadiness | null;
  settingValues: Record<string, string>;
  secretValues: Record<string, string>;
  persistedSettings: Record<string, SettingItem>;
  dirtyKeys: string[];
  saving: boolean;
  onValueChange: (configKey: string, value: string) => void;
  onSaveSection: (configKeys: string[]) => void;
}) {
  const { t } = useTranslation();
  const sectionConfigKeys = section.items.flatMap((item) => item.configKeys);
  const sectionDirtyKeys = sectionConfigKeys.filter((configKey) => dirtyKeys.includes(configKey));
  return (
    <Card>
      <CardHeader className="border-b pb-4">
        <div className="grid gap-4 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-start">
          <div className="flex min-w-0 items-center gap-3">
            <div className="grid size-8 place-items-center rounded-lg bg-muted text-muted-foreground">
              {kind === "api" ? <Database className="size-4" /> : null}
              {kind === "model" ? <Bot className="size-4" /> : null}
              {kind === "data" ? <Workflow className="size-4" /> : null}
              {kind === "user" ? <SlidersHorizontal className="size-4" /> : null}
              {kind === "system" ? <ShieldCheck className="size-4" /> : null}
            </div>
            <div className="min-w-0">
              <CardTitle className="truncate text-base">{t(section.titleKey)}</CardTitle>
            </div>
          </div>
          <div className="flex flex-wrap justify-start gap-2 sm:justify-end">
            <Button type="button" variant="outline" size="sm" onClick={() => onSaveSection(sectionConfigKeys)} disabled={saving || sectionDirtyKeys.length === 0}>
              {t("settings.saveSection")}
            </Button>
            <Badge variant={sectionDirtyKeys.length > 0 ? "outline" : "secondary"}>
              {sectionDirtyKeys.length > 0 ? t("settings.unsavedCount", { count: sectionDirtyKeys.length }) : t("settings.editable")}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="divide-y px-0">
        {section.items.map((item) => (
          <SettingsCatalogRow
            key={item.id}
            label={t(item.labelKey)}
            detail={t(item.detailKey)}
            scope={t(item.scopeKey)}
            source={t(item.sourceKey)}
            configKeys={item.configKeys}
            settingValues={settingValues}
            secretValues={secretValues}
            persistedSettings={persistedSettings}
            dirtyKeys={dirtyKeys}
            onValueChange={onValueChange}
            status={settingsEntryStatus(item.id, readiness, optionsReadiness)}
            statusLabel={settingsEntryStatusLabel(item.id, readiness, optionsReadiness, t)}
          />
        ))}
      </CardContent>
    </Card>
  );
}

function PreflightRow({ label, ready, detail }: { label: string; ready: boolean; detail: string }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-lg bg-background px-3 py-2 text-xs">
      <span className="font-medium">{label}</span>
      <span className="min-w-0 truncate text-muted-foreground">{detail}</span>
      <Badge variant={ready ? "secondary" : "outline"}>{ready ? "OK" : "Wait"}</Badge>
    </div>
  );
}

function SettingsCatalogRow({
  label,
  detail,
  scope,
  source,
  configKeys,
  settingValues,
  secretValues,
  persistedSettings,
  dirtyKeys,
  onValueChange,
  status,
  statusLabel,
}: {
  label: string;
  detail: string;
  scope: string;
  source: string;
  configKeys: string[];
  settingValues: Record<string, string>;
  secretValues: Record<string, string>;
  persistedSettings: Record<string, SettingItem>;
  dirtyKeys: string[];
  onValueChange: (configKey: string, value: string) => void;
  status: "ready" | "not-ready" | "entry";
  statusLabel: string;
}) {
  const { t } = useTranslation();
  return (
    <article className="grid gap-4 p-4 lg:grid-cols-[minmax(260px,0.75fr)_minmax(0,1fr)] lg:items-start">
      <div className="min-w-0 lg:pr-4">
        <div className="flex flex-wrap items-start gap-2">
          <div className="flex min-w-0 flex-wrap items-center gap-2 lg:flex-1">
            <strong className="text-sm">{label}</strong>
            <Badge variant="secondary">{scope}</Badge>
          </div>
          <Badge variant={status === "ready" ? "default" : "outline"} className="h-fit">
            {statusLabel}
          </Badge>
        </div>
        <p className="mt-1 text-sm leading-6 text-muted-foreground">{detail}</p>
        <div className="mt-2 flex flex-wrap gap-1.5">
          <Badge variant="outline">{source}</Badge>
          {configKeys.map((configKey) => (
            <Badge key={configKey} variant="secondary" className="font-mono text-[0.68rem]">
              {configKey}
            </Badge>
          ))}
        </div>
      </div>
      <div className="grid gap-3">
        {configKeys.map((configKey) => {
          const secret = isSecretConfigKey(configKey);
          return (
            <label key={configKey} className="grid gap-2 sm:grid-cols-[minmax(180px,0.48fr)_minmax(0,1fr)] sm:items-start">
              <span className="pt-2 font-mono text-[0.68rem] text-muted-foreground">{configKey}</span>
              <div className="grid gap-1.5">
              <Input
                type={secret ? "password" : configInputType(configKey)}
                value={secret ? secretValues[configKey] ?? "" : settingValues[configKey] ?? defaultConfigValue(configKey)}
                placeholder={secret && persistedSettings[configKey]?.has_value ? t("settings.secretAlreadySaved") : configPlaceholder(configKey)}
                onChange={(event) => onValueChange(configKey, event.target.value)}
              />
              <span className="text-xs text-muted-foreground">
                {dirtyKeys.includes(configKey) ? t("settings.dirty") : persistedSettings[configKey] ? t("settings.persisted") : t("settings.defaultValue")}
                {secret ? ` · ${t("settings.secretWriteOnly")}` : ""}
              </span>
              </div>
            </label>
          );
        })}
      </div>
    </article>
  );
}

function isSecretConfigKey(configKey: string) {
  return /API_KEY|SECRET|TOKEN|PASSWORD|CREDENTIAL/i.test(configKey);
}

function configInputType(configKey: string) {
  if (/ENABLED$/i.test(configKey)) return "text";
  if (/SECONDS|MINUTES|ROUNDS|RETRIES|TTL|TEMPERATURE|THRESHOLD/i.test(configKey)) return "text";
  if (/URL$/i.test(configKey) || /BASE_URL/i.test(configKey)) return "url";
  return "text";
}

function configPlaceholder(configKey: string) {
  if (isSecretConfigKey(configKey)) return "••••••••";
  return defaultConfigValue(configKey) || configKey;
}

function defaultConfigValue(configKey: string) {
  const defaults: Record<string, string> = {
    AQUANTLENS_SERVICE_NAME: "AQuantLens API",
    AQUANTLENS_MARKET_DATA_PROVIDER: "polygon",
    AQUANTLENS_POLYGON_BASE_URL: "https://api.polygon.io",
    AQUANTLENS_MANUAL_MARKET_SYNC_ENABLED: "true",
    AQUANTLENS_PROVIDER_MAX_RETRIES: "2",
    AQUANTLENS_PROVIDER_RETRY_BACKOFF_SECONDS: "1.0",
    AQUANTLENS_PROVIDER_SYNC_STALE_AFTER_MINUTES: "1440",
    AQUANTLENS_PROVIDER_SYNC_FAILURE_RATE_THRESHOLD: "0.5",
    AQUANTLENS_SCHEDULER_TARGETS: "SPY:1d:2",
    AQUANTLENS_SCHEDULER_INTERVAL_SECONDS: "300",
    AQUANTLENS_DATABASE_URL: "sqlite:///./aquantlens_us.db",
    AQUANTLENS_REDIS_URL: "redis://127.0.0.1:6379/0",
    AQUANTLENS_REALTIME_MARKET_PUBLISH_ENABLED: "false",
    AQUANTLENS_REALTIME_MARKET_TTL_SECONDS: "300",
    VITE_API_BASE_URL: "http://127.0.0.1:8022",
    TRADINGAGENTS_LLM_PROVIDER: "openai",
    TRADINGAGENTS_DEEP_THINK_LLM: "gpt-5.5",
    TRADINGAGENTS_QUICK_THINK_LLM: "gpt-5.4-mini",
    TRADINGAGENTS_OUTPUT_LANGUAGE: "Chinese",
    TRADINGAGENTS_MAX_DEBATE_ROUNDS: "1",
    TRADINGAGENTS_MAX_RISK_ROUNDS: "1",
    TRADINGAGENTS_TEMPERATURE: "",
    "analysis.language": "zh",
    "analysis.depth": "standard",
    "analysis.analyst_set": "macro-options",
    "research.watchlist": SUPPORTED_SYMBOLS.slice(0, 6).join(","),
    "market.refresh": "manual",
    "options.sync-chain": "manual",
    "data_vendors.core_stock_apis": "yfinance",
    "data_vendors.macro_data": "fred",
    "data_vendors.news_data": "yfinance",
  };
  return defaults[configKey] ?? "";
}

function settingCategory(configKey: string, catalog: ReturnType<typeof getSettingsCatalog>) {
  const sectionGroups: Array<[string, SettingsCatalogSection[]]> = [
    ["api", catalog.apiSections],
    ["model", catalog.modelSections],
    ["data", catalog.dataSections],
    ["user", catalog.userSections],
    ["system", catalog.systemSections],
  ];
  for (const [category, sections] of sectionGroups) {
    if (sections.some((section) => section.items.some((item) => item.configKeys.includes(configKey)))) {
      return category;
    }
  }
  return "general";
}

function settingsEntryStatus(
  itemId: string,
  readiness?: ProviderReadiness | null,
  optionsReadiness?: ProviderReadiness | null,
): "ready" | "not-ready" | "entry" {
  if (itemId === "polygon") {
    return readiness?.ready || optionsReadiness?.ready ? "ready" : "not-ready";
  }
  return "entry";
}

function settingsEntryStatusLabel(
  itemId: string,
  readiness: ProviderReadiness | null | undefined,
  optionsReadiness: ProviderReadiness | null | undefined,
  t: ReturnType<typeof useTranslation>["t"],
) {
  const status = settingsEntryStatus(itemId, readiness, optionsReadiness);
  if (status === "ready") return t("settings.entryStatus.ready");
  if (status === "not-ready") return t("settings.entryStatus.notReady");
  return t("settings.entryStatus.entry");
}

function ResearchContextCard({
  symbol,
  bars,
  optionSnapshots,
  optionContracts,
  providerReadiness,
  optionsProviderReadiness,
  analysisConfig,
  latestReport,
  onNavigate,
}: {
  symbol: string;
  bars: MarketBar[];
  optionSnapshots: OptionSnapshot[];
  optionContracts: OptionContract[];
  providerReadiness: ProviderReadiness | null;
  optionsProviderReadiness: ProviderReadiness | null;
  analysisConfig: Pick<AnalysisStartPayload, "analysisDate" | "llmProvider" | "model" | "depth" | "analystSet" | "researchTemplate">;
  latestReport: ReportListItem | null;
  onNavigate: (page: PageKey) => void;
}) {
  const { t } = useTranslation();
  const sortedBars = [...bars].sort((left, right) => new Date(left.timestamp).getTime() - new Date(right.timestamp).getTime());
  const latestBar = sortedBars[sortedBars.length - 1] ?? null;
  const optionVolume = optionSnapshots.reduce((sum, snapshot) => sum + snapshot.volume, 0);
  const optionOpenInterest = optionSnapshots.reduce((sum, snapshot) => sum + (snapshot.open_interest ?? 0), 0);
  const providerReady = Boolean(providerReadiness?.ready || optionsProviderReadiness?.ready);
  const briefItems = [
    {
      key: "market",
      ready: bars.length > 0,
      label: t("analysis.brief.market"),
      detail: latestBar
        ? t("analysis.brief.marketReady", { count: bars.length, close: latestBar.close.toFixed(2) })
        : t("analysis.brief.marketMissing"),
      action: () => onNavigate("market"),
      actionLabel: t("analysis.context.openMarket"),
    },
    {
      key: "options",
      ready: optionSnapshots.length > 0 || optionContracts.length > 0,
      label: t("analysis.brief.options"),
      detail:
        optionSnapshots.length > 0
          ? t("analysis.brief.optionsReady", { snapshots: optionSnapshots.length, contracts: optionContracts.length })
          : t("analysis.brief.optionsMissing", { contracts: optionContracts.length }),
      action: () => onNavigate("options"),
      actionLabel: t("analysis.context.openOptions"),
    },
    {
      key: "provider",
      ready: providerReady,
      label: t("analysis.brief.provider"),
      detail: providerReady ? t("analysis.brief.providerReady") : t("analysis.brief.providerMissing"),
      action: () => onNavigate("settings"),
      actionLabel: t("analysis.context.configure"),
    },
    {
      key: "report",
      ready: Boolean(latestReport),
      label: t("analysis.brief.priorReport"),
      detail: latestReport
        ? t("analysis.brief.priorReportReady", { symbol: latestReport.symbol, confidence: (latestReport.confidence * 100).toFixed(0) })
        : t("analysis.brief.priorReportMissing"),
      action: () => onNavigate("reports"),
      actionLabel: t("analysis.context.openReports"),
    },
  ];
  const readyItemCount = briefItems.filter((item) => item.ready).length;
  const briefTone = readyItemCount >= 3 ? "default" : "secondary";

  return (
    <Card>
      <CardHeader>
        <div className="flex min-w-0 items-center gap-2">
          <div className="grid size-9 place-items-center rounded-lg bg-muted text-muted-foreground">
            <Workflow className="size-4" />
          </div>
          <div className="min-w-0">
            <CardTitle>{t("analysis.context.title")}</CardTitle>
          </div>
        </div>
      </CardHeader>
      <CardContent className="grid gap-4">
        <section className="rounded-lg border bg-background p-3">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <Badge variant={briefTone}>{t("analysis.brief.phase")}</Badge>
                <Badge variant="outline">{analysisConfig.depth}</Badge>
                <Badge variant="outline">{analysisConfig.analystSet}</Badge>
                <Badge variant="outline">{t(`analysis.templates.${analysisConfig.researchTemplate}`)}</Badge>
              </div>
              <h3 className="mt-3 text-sm font-semibold">{t("analysis.brief.title", { symbol })}</h3>
              <p className="mt-2 text-sm leading-6 text-muted-foreground">
                {t("analysis.brief.description", {
                  date: analysisConfig.analysisDate,
                  model: `${analysisConfig.llmProvider} · ${analysisConfig.model}`,
                  ready: readyItemCount,
                  total: briefItems.length,
                })}
              </p>
            </div>
          </div>
          <div className="mt-3 grid grid-cols-4 gap-3 max-xl:grid-cols-2 max-sm:grid-cols-1">
            {briefItems.map((item) => (
              <div key={item.key} className="flex min-h-[132px] flex-col justify-between gap-3 rounded-lg border bg-card p-3">
                <div>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-sm font-semibold">{item.label}</span>
                    <Badge variant={item.ready ? "secondary" : "outline"}>
                      {item.ready ? t("analysis.brief.ready") : t("analysis.brief.needsWork")}
                    </Badge>
                  </div>
                  <p className="mt-2 text-xs leading-5 text-muted-foreground">{item.detail}</p>
                </div>
                {!item.ready ? (
                  <Button type="button" variant="outline" size="sm" onClick={item.action}>
                    {item.actionLabel}
                  </Button>
                ) : null}
              </div>
            ))}
          </div>
        </section>

        <div className="grid grid-cols-4 gap-3 max-xl:grid-cols-2 max-sm:grid-cols-1">
          <StatusCard
            label={t("analysis.context.market")}
            value={bars.length > 0 ? t("analysis.context.ready") : t("analysis.context.waiting")}
            detail={
              latestBar
                ? t("analysis.context.barsReady", {
                    count: bars.length,
                    close: latestBar.close.toFixed(2),
                    time: formatDate(latestBar.timestamp),
                  })
                : t("analysis.context.barsMissing")
            }
            status={bars.length > 0 ? "ready" : "missing"}
          />
          <StatusCard
            label={t("analysis.context.options")}
            value={optionSnapshots.length > 0 ? t("analysis.context.ready") : t("analysis.context.waiting")}
            detail={
              optionSnapshots.length
                ? t("analysis.context.optionsReady", {
                    count: optionSnapshots.length,
                    volume: optionVolume.toLocaleString(),
                  })
                : t("analysis.context.optionsMissing")
            }
            status={optionSnapshots.length > 0 ? "ready" : "missing"}
          />
          <StatusCard
            label={t("analysis.context.provider")}
            value={providerReady ? t("analysis.context.ready") : t("analysis.context.waiting")}
            detail={
              providerReady
                ? t("analysis.context.providerReady")
                : providerReadiness?.message ?? optionsProviderReadiness?.message ?? t("analysis.context.providerMissing")
            }
            status={providerReady ? "ready" : "missing"}
          />
          <StatusCard
            label={t("analysis.context.report")}
            value={latestReport ? latestReport.symbol : t("analysis.context.waiting")}
            detail={
              latestReport
                ? t("analysis.context.reportReady", {
                    symbol: latestReport.symbol,
                    confidence: (latestReport.confidence * 100).toFixed(0),
                  })
                : t("analysis.context.reportMissing")
            }
            status={latestReport ? "ready" : "missing"}
          />
        </div>

        <div className="grid grid-cols-4 gap-3 max-xl:grid-cols-2 max-sm:grid-cols-1">
          <MetricCard label={t("analysis.context.symbol")} value={symbol} helper={t("analysis.context.symbolHelper")} />
          <MetricCard label={t("analysis.context.optionOi")} value={optionOpenInterest.toLocaleString()} helper={t("analysis.context.optionOiHelper")} />
          <MetricCard label={t("analysis.context.optionContracts")} value={optionContracts.length.toLocaleString()} helper={t("analysis.context.optionContractsHelper")} />
          <MetricCard label={t("analysis.context.marketSource")} value={latestBar?.source ?? "-"} helper={latestBar ? formatDate(latestBar.timestamp) : t("analysis.context.noMarketSource")} />
        </div>

        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="outline" onClick={() => onNavigate("market")}>
            <CandlestickChart data-icon="inline-start" />
            {t("analysis.context.openMarket")}
          </Button>
          <Button type="button" variant="outline" onClick={() => onNavigate("options")}>
            <Activity data-icon="inline-start" />
            {t("analysis.context.openOptions")}
          </Button>
          <Button type="button" variant="outline" onClick={() => onNavigate("settings")}>
            <Settings data-icon="inline-start" />
            {t("analysis.context.configure")}
          </Button>
          <Button type="button" variant="outline" onClick={() => onNavigate("reports")}>
            <FileText data-icon="inline-start" />
            {t("analysis.context.openReports")}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function RunsPreview({ runs }: { runs: ProviderSyncRunItem[] }) {
  const { t } = useTranslation();
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("runs.recentDataTasks")}</CardTitle>
      </CardHeader>
      <CardContent>
      <SyncRunTable runs={runs.slice(0, 5)} compact />
      </CardContent>
    </Card>
  );
}

function RunOperationsStrip({
  latestAnalysisRun,
  latestProviderRun,
  summary,
  runningRuns,
  failedRuns,
}: {
  latestAnalysisRun: AnalysisRunItem | null;
  latestProviderRun: ProviderSyncRunItem | null;
  summary: ProviderSyncSummary | null;
  runningRuns: number;
  failedRuns: number;
}) {
  const { t } = useTranslation();
  const providerFailureRate = summary?.total_runs ? Math.round((summary.failed / summary.total_runs) * 100) : 0;

  return (
    <div className="grid grid-cols-4 gap-3 max-xl:grid-cols-2 max-sm:grid-cols-1">
      <StatusCard
        label={t("runs.ops.analysisLane")}
        value={latestAnalysisRun?.status ?? t("runs.noTaskRuns")}
        detail={latestAnalysisRun ? `${latestAnalysisRun.symbol} · ${latestAnalysisRun.model}` : t("runs.ops.waitingAnalysis")}
        status={runningRuns > 0 ? "warn" : failedRuns > 0 ? "bad" : "good"}
      />
      <StatusCard
        label={t("runs.ops.providerLane")}
        value={latestProviderRun?.status ?? t("runs.noTaskRuns")}
        detail={latestProviderRun ? `${latestProviderRun.provider} · ${latestProviderRun.sync_type}` : t("runs.ops.waitingProvider")}
        status={latestProviderRun?.status === "failed" ? "bad" : "good"}
      />
      <StatusCard
        label={t("runs.ops.failureRate")}
        value={`${providerFailureRate}%`}
        detail={summary ? `${summary.failed}/${summary.total_runs} ${t("runs.failed")}` : t("runs.ops.waitingSummary")}
        status={providerFailureRate > 0 ? "warn" : "good"}
      />
      <StatusCard
        label={t("runs.ops.latestWrite")}
        value={latestProviderRun ? latestProviderRun.rows_written.toLocaleString() : "0"}
        detail={latestProviderRun?.finished_at ? formatDate(latestProviderRun.finished_at) : t("runs.ops.notFinished")}
        status={latestProviderRun?.status === "failed" ? "bad" : "good"}
      />
    </div>
  );
}

function AnalysisRunTable({
  runs,
  onOpenReport,
  onRetryAnalysis,
  onInspectRun,
}: {
  runs: AnalysisRunItem[];
  onOpenReport: (reportId: string) => void;
  onRetryAnalysis: (analysisId: string) => void;
  onInspectRun: (run: AnalysisRunItem) => void;
}) {
  const { t } = useTranslation();
  const columns = useMemo<ColumnDef<AnalysisRunItem>[]>(
    () => [
      {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => {
          const status = normalizeRunStatus(row.original.status);
          return <Badge variant={status === "failed" ? "destructive" : "secondary"}>{row.original.status}</Badge>;
        },
      },
      {
        accessorKey: "symbol",
        header: "Symbol",
        cell: ({ row }) => <strong>{row.original.symbol}</strong>,
      },
      {
        accessorKey: "analysis_date",
        header: "Date",
      },
      {
        accessorKey: "created_at",
        header: t("runs.table.started"),
        cell: ({ row }) => formatDate(row.original.created_at),
      },
      {
        id: "duration",
        header: t("runs.table.duration"),
        cell: ({ row }) => formatDuration(row.original.created_at, row.original.updated_at),
      },
      {
        accessorKey: "llm_provider",
        header: "Provider",
      },
      {
        accessorKey: "model",
        header: "Model",
      },
      {
        accessorKey: "depth",
        header: "Depth",
      },
      {
        accessorKey: "report_id",
        header: t("runs.table.report"),
        cell: ({ row }) =>
          row.original.report_id ? (
            <Button type="button" variant="outline" size="sm" onClick={() => onOpenReport(row.original.report_id!)}>
              {t("runs.openReport")}
            </Button>
          ) : (
            "-"
          ),
      },
      {
        id: "action",
        header: t("runs.table.action"),
        cell: ({ row }) => {
          const status = normalizeRunStatus(row.original.status);
          if (status === "failed") {
            return (
              <div className="flex flex-wrap gap-2">
                <Button type="button" variant="outline" size="sm" onClick={() => onRetryAnalysis(row.original.analysis_id)}>
                  {t("runs.retry")}
                </Button>
                <Button type="button" variant="ghost" size="sm" onClick={() => onInspectRun(row.original)}>
                  {t("runs.errorDetail")}
                </Button>
              </div>
            );
          }
          if (status === "running") {
            return (
              <Button type="button" variant="ghost" size="sm" onClick={() => onInspectRun(row.original)}>
                {t("runs.viewProgress")}
              </Button>
            );
          }
          return (
            <Button type="button" variant="ghost" size="sm" onClick={() => onInspectRun(row.original)}>
              {t("runs.progress")}
            </Button>
          );
        },
      },
    ],
    [onOpenReport, onRetryAnalysis, onInspectRun, t],
  );
  const table = useReactTable({
    data: runs,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (!runs.length) return <p className="text-sm text-muted-foreground">{t("runs.noAnalysisRuns")}</p>;
  return (
    <Table>
      <TableHeader>
        {table.getHeaderGroups().map((headerGroup) => (
          <TableRow key={headerGroup.id}>
            {headerGroup.headers.map((header) => (
              <TableHead key={header.id}>
                {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
              </TableHead>
            ))}
          </TableRow>
        ))}
      </TableHeader>
      <TableBody>
        {table.getRowModel().rows.map((row) => (
          <TableRow key={row.id}>
            {row.getVisibleCells().map((cell) => (
              <TableCell key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function AnalysisRunDetailPanel({
  status,
  loading,
  error,
}: {
  status: AnalysisStatus | null;
  loading: boolean;
  error: string | null;
}) {
  const { t } = useTranslation();
  if (!status && !loading && !error) return null;
  return (
    <Card className="border-dashed">
        <CardHeader>
        <CardTitle>{t("runs.progressTitle")}</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {loading ? <p className="text-sm text-muted-foreground">{t("runs.loadingDetail")}</p> : null}
        {error ? (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}
        {status ? (
          <>
            <div className="grid grid-cols-4 gap-3 max-lg:grid-cols-2 max-sm:grid-cols-1">
              <WorkbenchMetric label="Symbol" value={status.symbol} />
              <WorkbenchMetric label="Status" value={status.status} />
              <WorkbenchMetric label="Asset" value={status.asset_type} />
              <WorkbenchMetric label="Language" value={status.language} />
            </div>
            <div className="flex flex-col gap-2">
              {status.progress.length > 0 ? (
                status.progress.map((event) => (
                  <article key={`${event.step}:${event.message}`} className="grid grid-cols-[12px_1fr] gap-3 rounded-lg border p-3">
                    <span className={`mt-1 size-2.5 rounded-full ${event.status === "completed" ? "bg-primary" : "bg-muted-foreground"}`} />
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <strong>{event.step}</strong>
                        <Badge variant="secondary">{event.status}</Badge>
                      </div>
                      <p className="mt-1 text-sm leading-6 text-muted-foreground">{event.message}</p>
                    </div>
                  </article>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">{t("runs.noProgress")}</p>
              )}
            </div>
          </>
        ) : null}
      </CardContent>
    </Card>
  );
}

function SyncRunTable({ runs, compact = false }: { runs: ProviderSyncRunItem[]; compact?: boolean }) {
  const { t } = useTranslation();
  const columns = useMemo<ColumnDef<ProviderSyncRunItem>[]>(
    () => [
      {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => (
          <Badge variant={row.original.status === "succeeded" ? "secondary" : "destructive"}>{row.original.status}</Badge>
        ),
      },
      {
        accessorKey: "provider",
        header: "Provider",
      },
      {
        accessorKey: "sync_type",
        header: t("runs.table.type"),
      },
      {
        accessorKey: "rows_written",
        header: t("runs.table.rows"),
        cell: ({ row }) => row.original.rows_written.toLocaleString(),
      },
      {
        accessorKey: "finished_at",
        header: t("runs.table.finished"),
        cell: ({ row }) => formatDate(row.original.finished_at ?? row.original.started_at),
      },
    ],
    [t],
  );
  const table = useReactTable({
    data: runs,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (!runs.length) return <p className="text-sm text-muted-foreground">{t("runs.noTaskRuns")}</p>;
  return (
    <Table className={compact ? "text-xs" : ""}>
        <TableHeader>
          {table.getHeaderGroups().map((headerGroup) => (
            <TableRow key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <TableHead key={header.id}>
                  {header.isPlaceholder ? null : flexRender(header.column.columnDef.header, header.getContext())}
                </TableHead>
              ))}
            </TableRow>
          ))}
        </TableHeader>
        <TableBody>
          {table.getRowModel().rows.map((row) => (
            <TableRow key={row.id}>
              {row.getVisibleCells().map((cell) => (
                <TableCell key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
  );
}

function normalizeRunStatus(status: string) {
  if (["completed", "succeeded", "success"].includes(status)) return "completed";
  if (["failed", "error", "cancelled"].includes(status)) return "failed";
  if (["queued", "running", "in_progress"].includes(status)) return "running";
  return status;
}

function formatDuration(startedAt: string, finishedAt: string) {
  const started = new Date(startedAt).getTime();
  const finished = new Date(finishedAt).getTime();
  if (!Number.isFinite(started) || !Number.isFinite(finished) || finished < started) return "-";
  const seconds = Math.round((finished - started) / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return `${minutes}m ${remainder}s`;
}

function WorkbenchMetric({ label, value, tone }: { label: string; value: string; tone?: "good" | "warn" | "bad" }) {
  return <MetricCard label={label} value={value} tone={tone} />;
}

function StatusRow({ label, value, status, detail }: { label: string; value: string; status: string; detail: string }) {
  return <StatusCard label={label} value={value} status={status} detail={detail} />;
}

function healthStatusLabel(status: string, t: ReturnType<typeof useTranslation>["t"]) {
  return t(`settings.health.${status}`, { defaultValue: status });
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}
