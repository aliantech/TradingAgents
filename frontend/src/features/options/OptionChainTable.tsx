import { Fragment, useMemo, useState } from "react";

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

type SelectedAction = "inspect" | "buy" | "sell";

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
  const [selectedAction, setSelectedAction] = useState<SelectedAction>("inspect");
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
  const averageIv = average(snapshots.map((snapshot) => snapshot.implied_volatility));
  const activeExpiry = buildExpiryMeta(expiry);

  function handleSelectContract(symbol: string, action: SelectedAction) {
    setSelectedSymbol(symbol);
    setSelectedAction(action);
  }

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

      <div className="underlying-strip">
        <div>
          <span>Underlying</span>
          <strong>{underlying}</strong>
        </div>
        <div>
          <span>参考价</span>
          <strong>{underlyingPrice ? formatOptionNumber(underlyingPrice) : "-"}</strong>
        </div>
        <div>
          <span>IV</span>
          <strong>{formatOptionPercent(averageIv)}</strong>
        </div>
        <div>
          <span>模式</span>
          <strong>Single · Research Only</strong>
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

      <div className="expiry-strip" aria-label="到期日">
        <button type="button" className="active">
          <strong>{activeExpiry.label}</strong>
          <span>{activeExpiry.daysLabel}</span>
          <em>{activeExpiry.kind}</em>
        </button>
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

      <div className={`option-chain-layout ${visibleRows.length === 0 ? "is-empty" : ""}`}>
        <div className="table-wrap option-chain-wrap">
          {visibleRows.length > 0 ? (
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
                  <Fragment key={row.strike}>
                    {row.isAtTheMoney && underlyingPrice !== null ? (
                      <tr className="current-price-marker">
                        <td colSpan={15}>Current price near {formatOptionNumber(underlyingPrice)}</td>
                      </tr>
                    ) : null}
                    <OptionRow
                      row={row}
                      selectedSymbol={selectedSymbol}
                      underlyingPrice={underlyingPrice}
                      onSelect={handleSelectContract}
                    />
                  </Fragment>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="empty-state option-table-empty">当前筛选没有可显示的期权行。</div>
          )}
        </div>

        <aside className="selected-contract-panel">
          <div className="preview-heading">
            <div>
              <h3>策略预览</h3>
              <p>Research Only · 不创建真实订单</p>
            </div>
            <span>{actionLabel(selectedAction)}</span>
          </div>
          {selectedContract ? (
            <>
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
              <div className="premium-preview">
                <span>Estimated Premium</span>
                <strong>{estimatePremium(selectedContract, selectedAction)}</strong>
              </div>
            </>
          ) : (
            <p>点击 Bid 形成 Sell 预览，点击 Ask 形成 Buy 预览，点击 Last 只查看合约。</p>
          )}
        </aside>
      </div>
    </section>
  );
}

function OptionRow({
  row,
  selectedSymbol,
  underlyingPrice,
  onSelect,
}: {
  row: OptionChainRow;
  selectedSymbol: string;
  underlyingPrice: number | null;
  onSelect: (symbol: string, action: SelectedAction) => void;
}) {
  const callMoneyness = getMoneynessClass("call", row.strike, underlyingPrice);
  const putMoneyness = getMoneynessClass("put", row.strike, underlyingPrice);

  return (
    <tr className={row.isAtTheMoney ? "atm-row" : ""}>
      <OptionValue value={row.call?.delta} digits={4} selected={row.call?.option_symbol === selectedSymbol} tone={callMoneyness} />
      <td className={callMoneyness}>{formatOptionPercent(row.call?.implied_volatility)}</td>
      <td className={callMoneyness}>{row.call?.open_interest?.toLocaleString() ?? "-"}</td>
      <td className={callMoneyness}>{row.call?.volume.toLocaleString() ?? "-"}</td>
      <ActionCell snapshot={row.call} value={row.call?.last} action="inspect" tone={callMoneyness} onSelect={onSelect} />
      <ActionCell snapshot={row.call} value={row.call?.bid} action="sell" tone={callMoneyness} onSelect={onSelect} />
      <ActionCell snapshot={row.call} value={row.call?.ask} action="buy" tone={callMoneyness} onSelect={onSelect} />
      <td className="strike-col">{formatOptionNumber(row.strike)}</td>
      <ActionCell snapshot={row.put} value={row.put?.bid} action="sell" tone={putMoneyness} onSelect={onSelect} />
      <ActionCell snapshot={row.put} value={row.put?.ask} action="buy" tone={putMoneyness} onSelect={onSelect} />
      <ActionCell snapshot={row.put} value={row.put?.last} action="inspect" tone={putMoneyness} onSelect={onSelect} />
      <td className={putMoneyness}>{row.put?.volume.toLocaleString() ?? "-"}</td>
      <td className={putMoneyness}>{row.put?.open_interest?.toLocaleString() ?? "-"}</td>
      <td className={putMoneyness}>{formatOptionPercent(row.put?.implied_volatility)}</td>
      <OptionValue value={row.put?.delta} digits={4} selected={row.put?.option_symbol === selectedSymbol} tone={putMoneyness} />
    </tr>
  );
}

function OptionValue({
  value,
  digits,
  selected,
  tone,
}: {
  value: number | null | undefined;
  digits: number;
  selected: boolean;
  tone: string;
}) {
  return <td className={`${tone} ${selected ? "selected-cell" : ""}`}>{formatOptionNumber(value, digits)}</td>;
}

function ActionCell({
  snapshot,
  value,
  action,
  tone,
  onSelect,
}: {
  snapshot?: OptionSnapshot;
  value: number | null | undefined;
  action: SelectedAction;
  tone: string;
  onSelect: (symbol: string, action: SelectedAction) => void;
}) {
  if (!snapshot) return <td className={tone}>-</td>;
  return (
    <td className={`action-cell ${tone}`}>
      <button type="button" onClick={() => onSelect(snapshot.option_symbol, action)} title={actionLabel(action)}>
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

function average(values: Array<number | null | undefined>) {
  const numbers = values.filter((value): value is number => typeof value === "number" && Number.isFinite(value));
  if (numbers.length === 0) return null;
  return numbers.reduce((sum, value) => sum + value, 0) / numbers.length;
}

function buildExpiryMeta(expiry: string) {
  const expiryDate = new Date(`${expiry}T00:00:00`);
  const today = new Date();
  const days = Number.isFinite(expiryDate.getTime())
    ? Math.max(0, Math.ceil((expiryDate.getTime() - today.getTime()) / 86_400_000))
    : null;
  return {
    label: expiry || "-",
    daysLabel: days === null ? "-" : `${days}d`,
    kind: days !== null && days <= 10 ? "W" : "M",
  };
}

function getMoneynessClass(side: "call" | "put", strike: number, underlyingPrice: number | null) {
  if (underlyingPrice === null) return "";
  const isItm = side === "call" ? strike < underlyingPrice : strike > underlyingPrice;
  return isItm ? "itm-cell" : "otm-cell";
}

function actionLabel(action: SelectedAction) {
  const labels: Record<SelectedAction, string> = {
    buy: "Buy Preview",
    sell: "Sell Preview",
    inspect: "Inspect",
  };
  return labels[action];
}

function estimatePremium(snapshot: OptionSnapshot, action: SelectedAction) {
  const price = action === "buy" ? snapshot.ask : action === "sell" ? snapshot.bid : snapshot.last;
  if (typeof price !== "number" || !Number.isFinite(price)) return "-";
  return `$${formatOptionNumber(price * 100)}`;
}
