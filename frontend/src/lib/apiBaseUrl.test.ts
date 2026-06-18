import { resolveApiBaseUrl } from "./apiBaseUrl.ts";

const publicBaseUrl = resolveApiBaseUrl({
  configuredBaseUrl: "http://127.0.0.1:8022",
  pageHostname: "dash.aquantlens.com",
});

if (publicBaseUrl !== "") {
  throw new Error("public frontend should use same-origin /api reverse proxy instead of visitor localhost");
}

const localBaseUrl = resolveApiBaseUrl({
  configuredBaseUrl: "http://127.0.0.1:8022",
  pageHostname: "127.0.0.1",
});

if (localBaseUrl !== "http://127.0.0.1:8022") {
  throw new Error("local frontend should keep an explicitly configured local API base URL");
}

const localDefaultBaseUrl = resolveApiBaseUrl({
  pageHostname: "127.0.0.1",
});

if (localDefaultBaseUrl !== "http://127.0.0.1:8022") {
  throw new Error("local frontend should default to the local FastAPI preview port when no env base URL is configured");
}

const publicDefaultBaseUrl = resolveApiBaseUrl({
  pageHostname: "dash.aquantlens.com",
});

if (publicDefaultBaseUrl !== "") {
  throw new Error("public frontend without explicit API base URL should use same-origin /api routes");
}
