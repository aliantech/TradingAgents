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

if (!catalog.modelSections.some((section) => section.id === "ai-models")) {
  throw new Error("settings catalog should expose AI model setting entries");
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
