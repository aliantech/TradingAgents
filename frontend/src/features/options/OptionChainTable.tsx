import { useMemo, useState } from "react";

import type { OptionSnapshot } from "../../lib/api";
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
  underlying: string;
  expiry: string;
  loading: boolean;
  syncing: boolean;
  error: string | null;
  onUnderlyingChange: (value: string) => void;
  onExpiryChange: (value: string) => void;
  onRefresh: () => void;
  onSync: () => void;
};

const DEFAULT_UNDERLYING_PRICE: Record<string, number> = {
  SPY: 550,
  QQQ: 480,
  SPX: 5500,
};

export function OptionChainTable({
  snapshots,
  underlying,
  expiry,
  loading,
  syncing,
  error,
  onUnderlyingChange,
  onExpiryChange,
  onRefresh,
  onSync,
}: OptionChainTableProps) {
  const [moneyness, setMoneyness] = useState<MoneynessFilter>("near");
  const [selectedSymbol, setSelectedSymbol] = useState<string>("");
  const underlyingPrice = DEFAULT_UNDERLYING_PRICE[underlying.toUpperCase()] ?? null;
  const rows = useMemo(() => groupOptionSnapshots(snapshots, underlyingPrice), [snapshots, underlyingPrice]);
  const visibleRows = useMemo(
    () => filterRowsByMoneyness(rows, moneyness, underlyingPrice),
    [rows, moneyness, underlyingPrice],
  );
  const selectedContract = snapshots.find((snapshot) => snapshot.option_symbol === selectedSymbol) ?? null;
  const totalVolume = snapshots.reduce((sum, snapshot) => sum + snapshot.volume, 0);
  const totalOpenInterest = snapshots.reduce((sum, snapshot) => sum + (snapshot.open_interest ?? 0), 0);
  const latestTimestamp = snapshots[0]?.timestamp;

  return (
    <section className="panel option-panel">
      <div className="panel-header option-header">
        <div>
          <h2>期权链</h2>
          <p>
            {underlying} · {expiry} · Call / Strike / Put
          </p>
        </div>
        <div className="option-actions">
          <button type="button" className="secondary-button" onClick={onRefresh} disabled={loading || syncing}>
            {loading ? "加载中" : "刷新"}
          </button>
          <button type="button" onClick={onSync} disabled={loading || syncing}>
            {syncing ? "同步中" : "同步期权链"}
          </button>
        </div>
      </div>

      <div className="option-toolbar">
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
        <div className="segmented-control" aria-label="期权链筛选">
          {[
            ["near", "近价"],
            ["all", "全部"],
            ["itm", "价内"],
            ["otm", "价外"],
          ].map(([value, label]) => (
            <button
              key={value}
              type="button"
              className={moneyness === value ? "active" : ""}
              onClick={() => setMoneyness(value as MoneynessFilter)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      <div className="option-summary">
        <Metric label="合约数" value={snapshots.length.toLocaleString()} />
        <Metric label="Volume" value={totalVolume.toLocaleString()} />
        <Metric label="Open Interest" value={totalOpenInterest.toLocaleString()} />
        <Metric label="更新时间" value={latestTimestamp ? new Date(latestTimestamp).toLocaleString() : "-"} />
      </div>

      {error ? <div className="alert">{error}</div> : null}
      {!error && !loading && snapshots.length === 0 ? (
        <div className="empty-state">暂无期权链快照。请先同步当前 underlying 与到期日，或检查 provider readiness。</div>
      ) : null}

      <div className="option-chain-layout">
        <div className="table-wrap option-chain-wrap">
          <table className="option-chain-table">
            <thead>
              <tr>
                <th colSpan={7} className="side-title call-side">
                  Call
                </th>
                <th className="strike-col">Strike</th>
                <th colSpan={7} className="side-title put-side">
                  Put
                </th>
              </tr>
              <tr>
                <th>Delta</th>
                <th>IV</th>
                <th>OI</th>
                <th>Vol</th>
                <th>Last</th>
                <th>Bid</th>
                <th>Ask</th>
                <th className="strike-col">行权价</th>
                <th>Bid</th>
                <th>Ask</th>
                <th>Last</th>
                <th>Vol</th>
                <th>OI</th>
                <th>IV</th>
                <th>Delta</th>
              </tr>
            </thead>
            <tbody>
              {visibleRows.map((row) => (
                <OptionRow key={row.strike} row={row} selectedSymbol={selectedSymbol} onSelect={setSelectedSymbol} />
              ))}
            </tbody>
          </table>
        </div>

        <aside className="selected-contract-panel">
          <h3>合约详情</h3>
          {selectedContract ? (
            <dl>
              <Detail label="合约" value={selectedContract.option_symbol} />
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
          ) : (
            <p>选择一个 Bid、Ask 或 Last 单元格查看合约详情。</p>
          )}
        </aside>
      </div>
    </section>
  );
}

function OptionRow({
  row,
  selectedSymbol,
  onSelect,
}: {
  row: OptionChainRow;
  selectedSymbol: string;
  onSelect: (symbol: string) => void;
}) {
  return (
    <tr className={row.isAtTheMoney ? "atm-row" : ""}>
      <OptionValue value={row.call?.delta} digits={4} selected={row.call?.option_symbol === selectedSymbol} />
      <td>{formatOptionPercent(row.call?.implied_volatility)}</td>
      <td>{row.call?.open_interest?.toLocaleString() ?? "-"}</td>
      <td>{row.call?.volume.toLocaleString() ?? "-"}</td>
      <ActionCell snapshot={row.call} value={row.call?.last} onSelect={onSelect} />
      <ActionCell snapshot={row.call} value={row.call?.bid} onSelect={onSelect} />
      <ActionCell snapshot={row.call} value={row.call?.ask} onSelect={onSelect} />
      <td className="strike-col">{formatOptionNumber(row.strike)}</td>
      <ActionCell snapshot={row.put} value={row.put?.bid} onSelect={onSelect} />
      <ActionCell snapshot={row.put} value={row.put?.ask} onSelect={onSelect} />
      <ActionCell snapshot={row.put} value={row.put?.last} onSelect={onSelect} />
      <td>{row.put?.volume.toLocaleString() ?? "-"}</td>
      <td>{row.put?.open_interest?.toLocaleString() ?? "-"}</td>
      <td>{formatOptionPercent(row.put?.implied_volatility)}</td>
      <OptionValue value={row.put?.delta} digits={4} selected={row.put?.option_symbol === selectedSymbol} />
    </tr>
  );
}

function OptionValue({ value, digits, selected }: { value: number | null | undefined; digits: number; selected: boolean }) {
  return <td className={selected ? "selected-cell" : ""}>{formatOptionNumber(value, digits)}</td>;
}

function ActionCell({
  snapshot,
  value,
  onSelect,
}: {
  snapshot?: OptionSnapshot;
  value: number | null | undefined;
  onSelect: (symbol: string) => void;
}) {
  if (!snapshot) return <td>-</td>;
  return (
    <td className="action-cell">
      <button type="button" onClick={() => onSelect(snapshot.option_symbol)}>
        {formatOptionNumber(value)}
      </button>
    </td>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </>
  );
}
