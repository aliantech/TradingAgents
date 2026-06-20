import { getSettingsCatalog } from "./settingsCatalog.ts";

const catalog = getSettingsCatalog();

if (!catalog.apiSections.some((section) => section.id === "market-data")) {
  throw new Error("settings catalog should expose market-data API configuration entries");
}

if (!catalog.apiSections.some((section) => section.id === "ai-models")) {
  throw new Error("settings catalog should expose AI model API configuration entries");
}

if (!catalog.userSections.some((section) => section.id === "research-preferences")) {
  throw new Error("settings catalog should expose user research preference entries");
}

if (!catalog.modelSections.some((section) => section.id === "runner-runtime")) {
  throw new Error("settings catalog should expose runner runtime setting entries");
}

const modelConfigKeys = catalog.modelSections.flatMap((section) => section.items).flatMap((item) => item.configKeys);
const requiredRunnerKeys = [
  "AQUANTLENS_TRADINGAGENTS_RUNNER_MODE",
  "AQUANTLENS_TRADINGAGENTS_LLM_PROVIDER",
  "AQUANTLENS_TRADINGAGENTS_QUICK_THINK_LLM",
  "AQUANTLENS_TRADINGAGENTS_DEEP_THINK_LLM",
  "AQUANTLENS_TRADINGAGENTS_OUTPUT_LANGUAGE",
  "AQUANTLENS_TRADINGAGENTS_SELECTED_ANALYSTS",
  "AQUANTLENS_TRADINGAGENTS_MAX_DEBATE_ROUNDS",
  "AQUANTLENS_TRADINGAGENTS_MAX_RISK_DISCUSS_ROUNDS",
];
for (const configKey of requiredRunnerKeys) {
  if (!modelConfigKeys.includes(configKey)) {
    throw new Error(`settings catalog should expose ${configKey} in model settings`);
  }
}

if (modelConfigKeys.some((configKey) => configKey.endsWith("_API_KEY"))) {
  throw new Error("model settings should not display secret API keys");
}

if (!catalog.dataSections.some((section) => section.id === "sync-runtime")) {
  throw new Error("settings catalog should expose data sync runtime entries");
}

if (!catalog.systemSections.some((section) => section.id === "storage-runtime")) {
  throw new Error("settings catalog should expose system storage runtime entries");
}

if (!catalog.apiSections.flatMap((section) => section.items).some((item) => item.configKeys.includes("VITE_API_BASE_URL"))) {
  throw new Error("settings catalog should expose the frontend API base URL");
}
