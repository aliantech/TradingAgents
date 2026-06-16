import type { OptionSnapshot } from "../../lib/api";

type OptionChainTableProps = {
  snapshots: OptionSnapshot[];
  underlying: string;
  expiry: string;
  loading: boolean;
  error: string | null;
  onUnderlyingChange: (value: string) => void;
  onExpiryChange: (value: string) => void;
  onRefresh: () => void;
};

export function OptionChainTable({
  snapshots,
  underlying,
  expiry,
  loading,
  error,
  onUnderlyingChange,
  onExpiryChange,
  onRefresh,
}: OptionChainTableProps) {
  const totalVolume = snapshots.reduce((sum, snapshot) => sum + snapshot.volume, 0);
  const totalOpenInterest = snapshots.reduce((sum, snapshot) => sum + (snapshot.open_interest ?? 0), 0);
  const latestTimestamp = snapshots[0]?.timestamp;

  return (
    <section className="panel option-panel">
      <div className="panel-header">
        <div>
          <h2>期权链</h2>
          <p>SPX/SPY/QQQ 与高流动性美股期权的 IV、Greeks、成交量和 OI 视图。</p>
        </div>
        <button type="button" onClick={onRefresh} disabled={loading}>
          {loading ? "加载中" : "刷新"}
        </button>
      </div>

      <div className="option-controls">
        <label>
          <span>Underlying</span>
          <select value={underlying} onChange={(event) => onUnderlyingChange(event.target.value)}>
            <option value="SPX">SPX</option>
            <option value="SPY">SPY</option>
            <option value="QQQ">QQQ</option>
          </select>
        </label>
        <label>
          <span>到期日</span>
          <input type="date" value={expiry} onChange={(event) => onExpiryChange(event.target.value)} />
        </label>
      </div>

      <div className="option-summary">
        <div>
          <span>合约数</span>
          <strong>{snapshots.length}</strong>
        </div>
        <div>
          <span>Volume</span>
          <strong>{totalVolume.toLocaleString()}</strong>
        </div>
        <div>
          <span>Open Interest</span>
          <strong>{totalOpenInterest.toLocaleString()}</strong>
        </div>
        <div>
          <span>更新时间</span>
          <strong>{latestTimestamp ? new Date(latestTimestamp).toLocaleString() : "-"}</strong>
        </div>
      </div>

      {error ? <div className="alert">{error}</div> : null}

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>合约</th>
              <th>Bid</th>
              <th>Ask</th>
              <th>Last</th>
              <th>Volume</th>
              <th>IV</th>
              <th>Delta</th>
              <th>Gamma</th>
              <th>Theta</th>
              <th>Vega</th>
              <th>OI</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {snapshots.map((snapshot) => (
              <tr key={snapshot.option_symbol}>
                <td>{snapshot.option_symbol}</td>
                <td>{snapshot.bid?.toFixed(2)}</td>
                <td>{snapshot.ask?.toFixed(2)}</td>
                <td>{snapshot.last?.toFixed(2)}</td>
                <td>{snapshot.volume.toLocaleString()}</td>
                <td>{snapshot.implied_volatility ? `${(snapshot.implied_volatility * 100).toFixed(1)}%` : "-"}</td>
                <td>{snapshot.delta?.toFixed(2)}</td>
                <td>{snapshot.gamma?.toFixed(3)}</td>
                <td>{snapshot.theta?.toFixed(2)}</td>
                <td>{snapshot.vega?.toFixed(2)}</td>
                <td>{snapshot.open_interest?.toLocaleString() ?? "-"}</td>
                <td>{snapshot.source}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {snapshots.length === 0 && !loading ? <p className="empty">暂无期权链数据。</p> : null}
      </div>
    </section>
  );
}
