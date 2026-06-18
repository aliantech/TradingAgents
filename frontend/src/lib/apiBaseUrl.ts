type ResolveApiBaseUrlInput = {
  configuredBaseUrl?: string;
  pageHostname?: string;
};

const DEFAULT_LOCAL_API_BASE_URL = "http://127.0.0.1:8022";

function isLocalHostname(hostname: string | undefined): boolean {
  return hostname === "localhost" || hostname === "127.0.0.1" || hostname === "::1";
}

function isLocalApiBaseUrl(baseUrl: string): boolean {
  try {
    const parsedUrl = new URL(baseUrl);
    return isLocalHostname(parsedUrl.hostname);
  } catch {
    return false;
  }
}

export function resolveApiBaseUrl({ configuredBaseUrl, pageHostname }: ResolveApiBaseUrlInput): string {
  if (!configuredBaseUrl) {
    return isLocalHostname(pageHostname) ? DEFAULT_LOCAL_API_BASE_URL : "";
  }

  if (!isLocalHostname(pageHostname) && isLocalApiBaseUrl(configuredBaseUrl)) {
    return "";
  }

  return configuredBaseUrl;
}
