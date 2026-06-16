import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { AnalysisPanel } from "../features/analysis/AnalysisPanel";
import { DataSyncPanel } from "../features/market-data/DataSyncPanel";
import { KlineChart } from "../features/market-data/KlineChart";
import { OptionChainTable } from "../features/options/OptionChainTable";
import { ReportHistory } from "../features/reports/ReportHistory";
import { ReportPanel } from "../features/reports/ReportPanel";
import { SettingsPanel } from "../features/settings/SettingsPanel";
import {
  getProviderRuntimeSettings,
  getMarketBars,
  getOptionChain,
  getProviderReadiness,
  getProviderSyncHealth,
  getProviderSyncSummary,
  getReport,
  listProviderSyncSummaryGroups,
  listProviderSyncRuns,
  listReports,
  startAnalysis,
  syncDailyBars,
  syncOptionChain,
  updateProviderRuntimeSettings,
  type AnalysisStatus,
  type MarketBar,
  type OptionSnapshot,
  type ProviderSyncRunItem,
  type ProviderReadiness,
  type ProviderRuntimeSettings,
  type ProviderSyncHealth,
  type ProviderSyncSummary,
  type ProviderSyncSummaryGroup,
  type ReportListItem,
  type ResearchReport,
} from "../lib/api";
import "./App.css";

export function App() {
  const { t, i18n } = useTranslation();
  const [symbol, setSymbol] = useState("SPY");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus | null>(null);
  const [activeReport, setActiveReport] = useState<ResearchReport | null>(null);
  const [reports, setReports] = useState<ReportListItem[]>([]);
  const [bars, setBars] = useState<MarketBar[]>([]);
  const [optionSnapshots, setOptionSnapshots] = useState<OptionSnapshot[]>([]);
  const [optionUnderlying, setOptionUnderlying] = useState("SPX");
  const [optionExpiry, setOptionExpiry] = useState("2026-06-17");
  const [optionsLoading, setOptionsLoading] = useState(false);
  const [optionsSyncing, setOptionsSyncing] = useState(false);
  const [optionsError, setOptionsError] = useState<string | null>(null);
  const [syncRuns, setSyncRuns] = useState<ProviderSyncRunItem[]>([]);
  const [syncSummary, setSyncSummary] = useState<ProviderSyncSummary | null>(null);
  const [syncGroups, setSyncGroups] = useState<ProviderSyncSummaryGroup[]>([]);
  const [syncHealth, setSyncHealth] = useState<ProviderSyncHealth | null>(null);
  const [providerReadiness, setProviderReadiness] = useState<ProviderReadiness | null>(null);
  const [syncProviderFilter, setSyncProviderFilter] = useState("");
  const [syncTypeFilter, setSyncTypeFilter] = useState("");
  const [syncStartedAfterFilter, setSyncStartedAfterFilter] = useState("");
  const [syncStartedBeforeFilter, setSyncStartedBeforeFilter] = useState("");
  const [syncLoading, setSyncLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncError, setSyncError] = useState<string | null>(null);
  const [runtimeSettings, setRuntimeSettings] = useState<ProviderRuntimeSettings | null>(null);
  const [settingsSaving, setSettingsSaving] = useState(false);
  const [settingsError, setSettingsError] = useState<string | null>(null);

  useEffect(() => {
    void loadInitialState();
  }, []);

  async function loadInitialState() {
    try {
      await Promise.all([
        loadMarketContext(symbol),
        loadOptionChain(optionUnderlying, optionExpiry),
        refreshReports(),
        refreshRuntimeSettings(),
      ]);
      await refreshSyncRuns();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "初始化数据加载失败，请检查后端服务是否已启动。");
    }
  }

  async function loadMarketContext(nextSymbol: string) {
    const chartSymbol = nextSymbol.toUpperCase() === "SPX" ? "SPY" : nextSymbol;
    const barsResponse = await getMarketBars(chartSymbol);
    setBars(barsResponse.bars);
  }

  async function loadOptionChain(nextUnderlying: string, nextExpiry: string) {
    setOptionsLoading(true);
    setOptionsError(null);
    try {
      const chainResponse = await getOptionChain(nextUnderlying, nextExpiry);
      setOptionSnapshots(chainResponse.snapshots);
      setOptionUnderlying(chainResponse.underlying_symbol);
      setOptionExpiry(chainResponse.expiry);
    } catch (caught) {
      setOptionsError(caught instanceof Error ? caught.message : "期权链加载失败。");
    } finally {
      setOptionsLoading(false);
    }
  }

  async function handleRefreshOptions() {
    await loadOptionChain(optionUnderlying, optionExpiry);
  }

  async function handleSyncOptions() {
    setOptionsSyncing(true);
    setOptionsError(null);
    try {
      const response = await syncOptionChain(optionUnderlying, optionExpiry);
      if (response.status !== "succeeded") {
        setOptionsError(response.error_message ?? "期权链同步未完成。");
      }
      await loadOptionChain(optionUnderlying, optionExpiry);
      await refreshSyncRuns();
    } catch (caught) {
      setOptionsError(caught instanceof Error ? caught.message : "期权链同步触发失败。");
    } finally {
      setOptionsSyncing(false);
    }
  }

  async function refreshReports() {
    const reportItems = await listReports();
    setReports(reportItems);
  }

  async function refreshRuntimeSettings() {
    const providerSettings = await getProviderRuntimeSettings();
    setRuntimeSettings(providerSettings);
  }

  async function handleSaveRuntimeSettings(input: { polygonApiKey: string; polygonBaseUrl: string }) {
    setSettingsSaving(true);
    setSettingsError(null);
    try {
      const providerSettings = await updateProviderRuntimeSettings(input);
      setRuntimeSettings(providerSettings);
      await loadSyncRuns({ showLoading: false });
      await loadOptionChain(optionUnderlying, optionExpiry);
    } catch (caught) {
      setSettingsError(caught instanceof Error ? caught.message : "设置保存失败。");
    } finally {
      setSettingsSaving(false);
    }
  }

  async function refreshSyncRuns() {
    return loadSyncRuns({ showLoading: false });
  }

  async function handleRefreshSyncRuns() {
    return loadSyncRuns({ showLoading: true });
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
        setSyncError(response.error_message ?? "同步未完成。");
      }
      await loadSyncRuns({ showLoading: false });
      await loadMarketContext(symbol);
    } catch (caught) {
      setSyncError(caught instanceof Error ? caught.message : "同步触发失败。");
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
      const [response, summary, groups, health, readiness] = await Promise.all([
        listProviderSyncRuns(filters),
        getProviderSyncSummary(filters),
        listProviderSyncSummaryGroups(filters),
        getProviderSyncHealth(filters),
        getProviderReadiness(readinessProvider),
      ]);
      setSyncRuns(response.runs);
      setSyncSummary(summary);
      setSyncGroups(groups.groups);
      setSyncHealth(health);
      setProviderReadiness(readiness);
    } catch (caught) {
      setSyncError(caught instanceof Error ? caught.message : "同步历史加载失败。");
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
      const status = await startAnalysis(symbol);
      setAnalysisStatus(status);
      await loadMarketContext(status.symbol);
      await refreshReports();
      await refreshSyncRuns();

      if (status.report_id) {
        const report = await getReport(status.report_id);
        setActiveReport(report);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "分析失败，请检查后端服务是否已启动。");
    } finally {
      setLoading(false);
    }
  }

  async function handleSelectReport(reportId: string) {
    setError(null);
    try {
      const report = await getReport(reportId);
      setActiveReport(report);
      setSymbol(report.symbol);
      await loadMarketContext(report.symbol);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "报告加载失败。");
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div>
          <h1>{t("title")}</h1>
          <p>{t("subtitle")}</p>
        </div>
        <nav>
          <a href="#analysis">AI 分析</a>
          <a href="#report">研究报告</a>
          <a href="#market">行情数据</a>
          <a href="#options">期权链</a>
          <a href="#sync">数据同步</a>
          <a href="#settings">设置</a>
        </nav>
        <button type="button" className="language-button" onClick={() => i18n.changeLanguage(i18n.language === "zh" ? "en" : "zh")}>
          {i18n.language === "zh" ? "English" : "中文"}
        </button>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">AQuantLens US Options Branch</p>
            <h2>美股与指数期权 AI 投研工作台</h2>
          </div>
          <div className="status-pill">Research Only</div>
        </header>

        <div className="grid">
          <div id="analysis" className="stack">
            <AnalysisPanel
              symbol={symbol}
              loading={loading}
              error={error}
              status={analysisStatus}
              onSymbolChange={setSymbol}
              onRunAnalysis={handleRunAnalysis}
            />
            <ReportHistory reports={reports} onSelectReport={handleSelectReport} />
          </div>

          <div id="report">
            <ReportPanel report={activeReport} />
          </div>

          <div id="market">
            <KlineChart bars={bars} />
          </div>

          <div id="options">
            <OptionChainTable
              snapshots={optionSnapshots}
              underlying={optionUnderlying}
              expiry={optionExpiry}
              loading={optionsLoading}
              syncing={optionsSyncing}
              error={optionsError}
              onUnderlyingChange={setOptionUnderlying}
              onExpiryChange={setOptionExpiry}
              onRefresh={() => void handleRefreshOptions()}
              onSync={() => void handleSyncOptions()}
            />
          </div>

          <div id="sync">
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
              onRefresh={() => void handleRefreshSyncRuns()}
              onSyncSample={() => void handleSyncSampleBars()}
            />
          </div>

          <div id="settings">
            <SettingsPanel
              settings={runtimeSettings}
              saving={settingsSaving}
              error={settingsError}
              onSave={(input) => void handleSaveRuntimeSettings(input)}
            />
          </div>
        </div>
      </section>
    </main>
  );
}

function toIsoDateTime(value: string) {
  return value ? new Date(value).toISOString() : undefined;
}
