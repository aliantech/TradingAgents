export type SettingsCatalogItem = {
  id: string;
  labelKey: string;
  detailKey: string;
  scopeKey: string;
  configKeys: string[];
  sourceKey: string;
  statusSource?: "polygon" | "local" | "runtime" | "planned";
};

export type SettingsCatalogSection = {
  id: string;
  titleKey: string;
  descriptionKey: string;
  items: SettingsCatalogItem[];
};

export type SettingsCatalog = {
  apiSections: SettingsCatalogSection[];
  modelSections: SettingsCatalogSection[];
  dataSections: SettingsCatalogSection[];
  userSections: SettingsCatalogSection[];
  systemSections: SettingsCatalogSection[];
};

export function getSettingsCatalog(): SettingsCatalog {
  return {
    apiSections: [
      {
        id: "market-data",
        titleKey: "settings.api.marketData.title",
        descriptionKey: "settings.api.marketData.description",
        items: [
          {
            id: "polygon",
            labelKey: "settings.api.items.polygon.label",
            detailKey: "settings.api.items.polygon.detail",
            scopeKey: "settings.api.scopes.marketAndOptions",
            configKeys: [
              "AQUANTLENS_MARKET_DATA_PROVIDER",
              "AQUANTLENS_POLYGON_API_KEY",
              "AQUANTLENS_POLYGON_BASE_URL",
            ],
            sourceKey: "settings.sources.backendConfig",
            statusSource: "polygon",
          },
          {
            id: "frontend-api",
            labelKey: "settings.api.items.frontendApi.label",
            detailKey: "settings.api.items.frontendApi.detail",
            scopeKey: "settings.api.scopes.frontendApi",
            configKeys: ["VITE_API_BASE_URL"],
            sourceKey: "settings.sources.frontendEnv",
            statusSource: "local",
          },
          {
            id: "manual-sync",
            labelKey: "settings.api.items.manualSync.label",
            detailKey: "settings.api.items.manualSync.detail",
            scopeKey: "settings.api.scopes.syncControl",
            configKeys: ["AQUANTLENS_MANUAL_MARKET_SYNC_ENABLED"],
            sourceKey: "settings.sources.backendConfig",
            statusSource: "runtime",
          },
        ],
      },
      {
        id: "ai-models",
        titleKey: "settings.api.aiModels.title",
        descriptionKey: "settings.api.aiModels.description",
        items: [
          {
            id: "openai",
            labelKey: "settings.api.items.openai.label",
            detailKey: "settings.api.items.openai.detail",
            scopeKey: "settings.api.scopes.primaryLlm",
            configKeys: ["OPENAI_API_KEY", "TRADINGAGENTS_LLM_PROVIDER", "TRADINGAGENTS_DEEP_THINK_LLM"],
            sourceKey: "settings.sources.tradingAgentsConfig",
            statusSource: "planned",
          },
          {
            id: "anthropic",
            labelKey: "settings.api.items.anthropic.label",
            detailKey: "settings.api.items.anthropic.detail",
            scopeKey: "settings.api.scopes.researchLlm",
            configKeys: ["ANTHROPIC_API_KEY"],
            sourceKey: "settings.sources.llmEnv",
            statusSource: "planned",
          },
          {
            id: "google",
            labelKey: "settings.api.items.google.label",
            detailKey: "settings.api.items.google.detail",
            scopeKey: "settings.api.scopes.alternativeLlm",
            configKeys: ["GOOGLE_API_KEY"],
            sourceKey: "settings.sources.llmEnv",
            statusSource: "planned",
          },
          {
            id: "openai-compatible",
            labelKey: "settings.api.items.openaiCompatible.label",
            detailKey: "settings.api.items.openaiCompatible.detail",
            scopeKey: "settings.api.scopes.customLlm",
            configKeys: ["OPENAI_COMPATIBLE_API_KEY", "TRADINGAGENTS_LLM_BACKEND_URL"],
            sourceKey: "settings.sources.llmEnv",
            statusSource: "planned",
          },
        ],
      },
    ],
    modelSections: [
      {
        id: "ai-models",
        titleKey: "settings.api.aiModels.title",
        descriptionKey: "settings.api.aiModels.description",
        items: [
          {
            id: "openai",
            labelKey: "settings.api.items.openai.label",
            detailKey: "settings.api.items.openai.detail",
            scopeKey: "settings.api.scopes.primaryLlm",
            configKeys: ["OPENAI_API_KEY", "TRADINGAGENTS_LLM_PROVIDER", "TRADINGAGENTS_DEEP_THINK_LLM"],
            sourceKey: "settings.sources.tradingAgentsConfig",
            statusSource: "planned",
          },
          {
            id: "anthropic",
            labelKey: "settings.api.items.anthropic.label",
            detailKey: "settings.api.items.anthropic.detail",
            scopeKey: "settings.api.scopes.researchLlm",
            configKeys: ["ANTHROPIC_API_KEY"],
            sourceKey: "settings.sources.llmEnv",
            statusSource: "planned",
          },
          {
            id: "google",
            labelKey: "settings.api.items.google.label",
            detailKey: "settings.api.items.google.detail",
            scopeKey: "settings.api.scopes.alternativeLlm",
            configKeys: ["GOOGLE_API_KEY"],
            sourceKey: "settings.sources.llmEnv",
            statusSource: "planned",
          },
          {
            id: "openai-compatible",
            labelKey: "settings.api.items.openaiCompatible.label",
            detailKey: "settings.api.items.openaiCompatible.detail",
            scopeKey: "settings.api.scopes.customLlm",
            configKeys: ["OPENAI_COMPATIBLE_API_KEY", "TRADINGAGENTS_LLM_BACKEND_URL"],
            sourceKey: "settings.sources.llmEnv",
            statusSource: "planned",
          },
        ],
      },
      {
        id: "agent-reasoning",
        titleKey: "settings.model.reasoning.title",
        descriptionKey: "settings.model.reasoning.description",
        items: [
          {
            id: "thinking-models",
            labelKey: "settings.model.items.thinkingModels.label",
            detailKey: "settings.model.items.thinkingModels.detail",
            scopeKey: "settings.model.scopes.reasoning",
            configKeys: ["TRADINGAGENTS_QUICK_THINK_LLM", "TRADINGAGENTS_DEEP_THINK_LLM"],
            sourceKey: "settings.sources.tradingAgentsConfig",
            statusSource: "runtime",
          },
          {
            id: "debate-rounds",
            labelKey: "settings.model.items.debateRounds.label",
            detailKey: "settings.model.items.debateRounds.detail",
            scopeKey: "settings.model.scopes.debate",
            configKeys: ["TRADINGAGENTS_MAX_DEBATE_ROUNDS", "TRADINGAGENTS_MAX_RISK_ROUNDS"],
            sourceKey: "settings.sources.tradingAgentsConfig",
            statusSource: "runtime",
          },
          {
            id: "temperature",
            labelKey: "settings.model.items.temperature.label",
            detailKey: "settings.model.items.temperature.detail",
            scopeKey: "settings.model.scopes.sampling",
            configKeys: ["TRADINGAGENTS_TEMPERATURE"],
            sourceKey: "settings.sources.tradingAgentsConfig",
            statusSource: "runtime",
          },
        ],
      },
    ],
    dataSections: [
      {
        id: "macro-news",
        titleKey: "settings.api.macroNews.title",
        descriptionKey: "settings.api.macroNews.description",
        items: [
          {
            id: "fred",
            labelKey: "settings.api.items.fred.label",
            detailKey: "settings.api.items.fred.detail",
            scopeKey: "settings.api.scopes.macro",
            configKeys: ["FRED_API_KEY"],
            sourceKey: "settings.sources.dataflowEnv",
            statusSource: "planned",
          },
          {
            id: "alpha-vantage",
            labelKey: "settings.api.items.alphaVantage.label",
            detailKey: "settings.api.items.alphaVantage.detail",
            scopeKey: "settings.api.scopes.fundamentals",
            configKeys: ["ALPHA_VANTAGE_API_KEY"],
            sourceKey: "settings.sources.dataflowEnv",
            statusSource: "planned",
          },
          {
            id: "vendor-routing",
            labelKey: "settings.data.items.vendorRouting.label",
            detailKey: "settings.data.items.vendorRouting.detail",
            scopeKey: "settings.data.scopes.routing",
            configKeys: ["data_vendors.core_stock_apis", "data_vendors.macro_data", "data_vendors.news_data"],
            sourceKey: "settings.sources.tradingAgentsConfig",
            statusSource: "runtime",
          },
        ],
      },
      {
        id: "sync-runtime",
        titleKey: "settings.data.syncRuntime.title",
        descriptionKey: "settings.data.syncRuntime.description",
        items: [
          {
            id: "provider-retry",
            labelKey: "settings.data.items.providerRetry.label",
            detailKey: "settings.data.items.providerRetry.detail",
            scopeKey: "settings.data.scopes.retry",
            configKeys: ["AQUANTLENS_PROVIDER_MAX_RETRIES", "AQUANTLENS_PROVIDER_RETRY_BACKOFF_SECONDS"],
            sourceKey: "settings.sources.backendConfig",
            statusSource: "runtime",
          },
          {
            id: "sync-health",
            labelKey: "settings.data.items.syncHealth.label",
            detailKey: "settings.data.items.syncHealth.detail",
            scopeKey: "settings.data.scopes.health",
            configKeys: [
              "AQUANTLENS_PROVIDER_SYNC_STALE_AFTER_MINUTES",
              "AQUANTLENS_PROVIDER_SYNC_FAILURE_RATE_THRESHOLD",
            ],
            sourceKey: "settings.sources.backendConfig",
            statusSource: "runtime",
          },
          {
            id: "scheduler",
            labelKey: "settings.data.items.scheduler.label",
            detailKey: "settings.data.items.scheduler.detail",
            scopeKey: "settings.data.scopes.scheduler",
            configKeys: ["AQUANTLENS_SCHEDULER_TARGETS", "AQUANTLENS_SCHEDULER_INTERVAL_SECONDS"],
            sourceKey: "settings.sources.backendConfig",
            statusSource: "runtime",
          },
        ],
      },
    ],
    userSections: [
      {
        id: "research-preferences",
        titleKey: "settings.user.researchPreferences.title",
        descriptionKey: "settings.user.researchPreferences.description",
        items: [
          {
            id: "default-language",
            labelKey: "settings.user.items.defaultLanguage.label",
            detailKey: "settings.user.items.defaultLanguage.detail",
            scopeKey: "settings.user.scopes.output",
            configKeys: ["TRADINGAGENTS_OUTPUT_LANGUAGE", "analysis.language"],
            sourceKey: "settings.sources.userPreference",
            statusSource: "local",
          },
          {
            id: "default-depth",
            labelKey: "settings.user.items.defaultDepth.label",
            detailKey: "settings.user.items.defaultDepth.detail",
            scopeKey: "settings.user.scopes.analysis",
            configKeys: ["analysis.depth"],
            sourceKey: "settings.sources.userPreference",
            statusSource: "local",
          },
          {
            id: "default-team",
            labelKey: "settings.user.items.defaultTeam.label",
            detailKey: "settings.user.items.defaultTeam.detail",
            scopeKey: "settings.user.scopes.analysis",
            configKeys: ["analysis.analyst_set"],
            sourceKey: "settings.sources.userPreference",
            statusSource: "local",
          },
        ],
      },
      {
        id: "workspace-preferences",
        titleKey: "settings.user.workspacePreferences.title",
        descriptionKey: "settings.user.workspacePreferences.description",
        items: [
          {
            id: "watchlist",
            labelKey: "settings.user.items.watchlist.label",
            detailKey: "settings.user.items.watchlist.detail",
            scopeKey: "settings.user.scopes.workspace",
            configKeys: ["research.watchlist"],
            sourceKey: "settings.sources.userPreference",
            statusSource: "runtime",
          },
          {
            id: "risk-view",
            labelKey: "settings.user.items.riskView.label",
            detailKey: "settings.user.items.riskView.detail",
            scopeKey: "settings.user.scopes.workspace",
            configKeys: ["report.risk_factors", "report.confidence", "options.greeks"],
            sourceKey: "settings.sources.frontendState",
            statusSource: "local",
          },
          {
            id: "data-refresh",
            labelKey: "settings.user.items.dataRefresh.label",
            detailKey: "settings.user.items.dataRefresh.detail",
            scopeKey: "settings.user.scopes.workspace",
            configKeys: ["market.refresh", "options.sync-chain"],
            sourceKey: "settings.sources.frontendState",
            statusSource: "local",
          },
        ],
      },
    ],
    systemSections: [
      {
        id: "storage-runtime",
        titleKey: "settings.system.storage.title",
        descriptionKey: "settings.system.storage.description",
        items: [
          {
            id: "service",
            labelKey: "settings.system.items.service.label",
            detailKey: "settings.system.items.service.detail",
            scopeKey: "settings.system.scopes.runtime",
            configKeys: ["AQUANTLENS_SERVICE_NAME"],
            sourceKey: "settings.sources.backendConfig",
            statusSource: "runtime",
          },
          {
            id: "database",
            labelKey: "settings.system.items.database.label",
            detailKey: "settings.system.items.database.detail",
            scopeKey: "settings.system.scopes.persistence",
            configKeys: ["AQUANTLENS_DATABASE_URL"],
            sourceKey: "settings.sources.backendConfig",
            statusSource: "runtime",
          },
          {
            id: "redis",
            labelKey: "settings.system.items.redis.label",
            detailKey: "settings.system.items.redis.detail",
            scopeKey: "settings.system.scopes.cache",
            configKeys: ["AQUANTLENS_REDIS_URL"],
            sourceKey: "settings.sources.backendConfig",
            statusSource: "runtime",
          },
          {
            id: "realtime",
            labelKey: "settings.system.items.realtime.label",
            detailKey: "settings.system.items.realtime.detail",
            scopeKey: "settings.system.scopes.realtime",
            configKeys: ["AQUANTLENS_REALTIME_MARKET_PUBLISH_ENABLED", "AQUANTLENS_REALTIME_MARKET_TTL_SECONDS"],
            sourceKey: "settings.sources.backendConfig",
            statusSource: "runtime",
          },
        ],
      },
    ],
  };
}
