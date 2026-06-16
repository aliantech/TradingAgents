import { type FormEvent, useEffect, useState } from "react";

import type { ProviderRuntimeSettings } from "../../lib/api";

type SettingsPanelProps = {
  settings: ProviderRuntimeSettings | null;
  saving: boolean;
  error: string | null;
  onSave: (input: { polygonApiKey: string; polygonBaseUrl: string }) => void;
};

export function SettingsPanel({ settings, saving, error, onSave }: SettingsPanelProps) {
  const [polygonApiKey, setPolygonApiKey] = useState("");
  const [polygonBaseUrl, setPolygonBaseUrl] = useState(settings?.polygon_base_url ?? "https://api.polygon.io");

  useEffect(() => {
    if (settings?.polygon_base_url) {
      setPolygonBaseUrl(settings.polygon_base_url);
    }
  }, [settings?.polygon_base_url]);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onSave({ polygonApiKey, polygonBaseUrl });
    setPolygonApiKey("");
  }

  return (
    <section className="panel settings-panel">
      <div className="panel-header">
        <div>
          <h2>设置</h2>
          <p>本地运行时 provider 配置。API key 仅保存在当前后端进程内存，不写入文件或数据库。</p>
        </div>
        <span className={`sync-status ${settings?.polygon_configured ? "succeeded" : "failed"}`}>
          {settings?.polygon_configured ? "Polygon ready" : "Not ready"}
        </span>
      </div>

      <form className="settings-form" onSubmit={handleSubmit}>
        <label>
          <span>Polygon / Massive API Key</span>
          <input
            type="password"
            value={polygonApiKey}
            autoComplete="off"
            placeholder={settings?.polygon_configured ? "已配置，输入新 key 可覆盖" : "输入 API key"}
            onChange={(event) => setPolygonApiKey(event.target.value)}
          />
        </label>
        <label>
          <span>Base URL</span>
          <input value={polygonBaseUrl} onChange={(event) => setPolygonBaseUrl(event.target.value)} />
        </label>
        <button type="submit" disabled={saving || (!polygonApiKey.trim() && !polygonBaseUrl.trim())}>
          {saving ? "保存中" : "保存设置"}
        </button>
      </form>

      {settings ? <p className="settings-message">{settings.message}</p> : null}
      {error ? <div className="alert">{error}</div> : null}
    </section>
  );
}
