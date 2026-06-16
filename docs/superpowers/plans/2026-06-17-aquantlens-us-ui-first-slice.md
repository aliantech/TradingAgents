# AQuantLens US UI First Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the first narrow UI slice from the approved AQuantLens US UI design: focused app shell refinement plus a non-bloated options-chain experience.

**Architecture:** Keep the existing React/Vite app and existing backend API adapters. Refactor only the option-chain surface and layout structure needed to make the current MVP feel like a research terminal. Do not introduce Tailwind, shadcn/ui, TanStack Table, or lightweight-charts in this slice; adding dependencies is deferred until there is a specific component that needs them.

**Tech Stack:** React, TypeScript, Vite, plain CSS, existing `frontend/src/lib/api.ts` types.

---

## Scope Guard

This slice implements only:

- Focused app-shell/navigation copy and layout cleanup.
- Option snapshot grouping utilities.
- A Call / Strike / Put option-chain table with moneyness filtering.
- Selected contract details.
- Empty/error states that distinguish no data from loading and failure.
- TypeScript build verification.

This slice explicitly does not implement:

- Dashboard.
- shadcn/ui or Tailwind installation.
- TanStack Table.
- lightweight-charts.
- Reports redesign.
- Runs page split.
- Settings page.
- Paper trading, broker actions, learning content, or A-share/HK workflows.

## File Structure

- Modify `frontend/src/app/App.tsx`: keep existing data loading, but change nav labels and default option expiry handling only if needed.
- Modify `frontend/src/app/App.css`: add focused terminal layout and option-chain styles; remove styling only when replaced by equivalent local styles.
- Create `frontend/src/features/options/optionChain.ts`: pure utility functions for grouping snapshots and formatting option values.
- Modify `frontend/src/features/options/OptionChainTable.tsx`: use the utility module, add moneyness filter, symmetric Call/Strike/Put table, and selected contract panel.
- Optionally modify `frontend/src/lib/api.ts`: only if type fields are missing for the UI; do not change endpoint paths.

## Task 1: Add Pure Option-Chain Utilities

**Files:**

- Create: `frontend/src/features/options/optionChain.ts`
- Modify: none
- Test: TypeScript build in Task 5

- [ ] **Step 1: Create the utility module**

Create `frontend/src/features/options/optionChain.ts` with this content:

```ts
import type { OptionSnapshot } from "../../lib/api";

export type OptionSide = "call" | "put";
export type MoneynessFilter = "near" | "all" | "itm" | "otm";

export type OptionChainRow = {
  strike: number;
  call?: OptionSnapshot;
  put?: OptionSnapshot;
  isAtTheMoney: boolean;
};

export function inferOptionSide(snapshot: OptionSnapshot): OptionSide | null {
  const compact = snapshot.option_symbol.toUpperCase().replace(/^O:/, "");
  const occMatch = compact.match(/^(.+?)(\d{6})([CP])(\d{8})$/);
  const side = occMatch?.[3];
  if (side === "C") return "call";
  if (side === "P") return "put";
  return null;
}

export function inferStrike(snapshot: OptionSnapshot): number | null {
  const symbol = snapshot.option_symbol.toUpperCase().replace(/^O:/, "");
  const occStrike = symbol.match(/^(.+?)(\d{6})([CP])(\d{8})$/);
  if (occStrike) {
    return Number(occStrike[4]) / 1000;
  }

  const looseStrike = symbol.match(/(\d+(?:\.\d+)?)$/);
  if (looseStrike) {
    return Number(looseStrike[1]);
  }

  return null;
}

export function groupOptionSnapshots(snapshots: OptionSnapshot[], underlyingPrice?: number | null): OptionChainRow[] {
  const rowsByStrike = new Map<number, OptionChainRow>();

  for (const snapshot of snapshots) {
    const strike = inferStrike(snapshot);
    const side = inferOptionSide(snapshot);
    if (strike === null || side === null || !Number.isFinite(strike)) continue;

    const row = rowsByStrike.get(strike) ?? {
      strike,
      isAtTheMoney: false,
    };

    if (side === "call" && !row.call) row.call = snapshot;
    if (side === "put" && !row.put) row.put = snapshot;
    rowsByStrike.set(strike, row);
  }

  const rows = Array.from(rowsByStrike.values()).sort((left, right) => left.strike - right.strike);
  const atmIndex = findNearestStrikeIndex(rows, underlyingPrice);

  return rows.map((row, index) => ({
    ...row,
    isAtTheMoney: index === atmIndex,
  }));
}

export function filterRowsByMoneyness(
  rows: OptionChainRow[],
  filter: MoneynessFilter,
  underlyingPrice?: number | null,
): OptionChainRow[] {
  if (filter === "all") return rows;
  if (rows.length === 0) return rows;

  const price = typeof underlyingPrice === "number" && Number.isFinite(underlyingPrice) ? underlyingPrice : null;
  if (filter === "near") {
    const atmIndex = rows.findIndex((row) => row.isAtTheMoney);
    const center = atmIndex >= 0 ? atmIndex : Math.floor(rows.length / 2);
    const radius = 8;
    return rows.slice(Math.max(0, center - radius), Math.min(rows.length, center + radius + 1));
  }

  if (price === null) return rows;

  return rows.filter((row) => {
    const hasItmCall = Boolean(row.call && row.strike < price);
    const hasItmPut = Boolean(row.put && row.strike > price);
    const hasOtmCall = Boolean(row.call && row.strike >= price);
    const hasOtmPut = Boolean(row.put && row.strike <= price);
    return filter === "itm" ? hasItmCall || hasItmPut : hasOtmCall || hasOtmPut;
  });
}

export function formatOptionNumber(value: number | null | undefined, digits = 2) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "-";
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value);
}

export function formatOptionPercent(value: number | null | undefined) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "-";
  const percent = Math.abs(value) <= 1 ? value * 100 : value;
  return `${formatOptionNumber(percent, 1)}%`;
}

function findNearestStrikeIndex(rows: OptionChainRow[], underlyingPrice?: number | null) {
  if (typeof underlyingPrice !== "number" || !Number.isFinite(underlyingPrice) || rows.length === 0) {
    return -1;
  }

  return rows.reduce((nearestIndex, row, index) => {
    const nearest = rows[nearestIndex];
    if (!nearest) return index;
    const distance = Math.abs(row.strike - underlyingPrice);
    const nearestDistance = Math.abs(nearest.strike - underlyingPrice);
    return distance < nearestDistance ? index : nearestIndex;
  }, 0);
}
```

- [ ] **Step 2: Run the frontend build**

Run:

```bash
cd frontend
npm run build
```

Expected: build passes. If dependencies are not installed in the current environment, run this verification on `ssh yasin-ubuntu` according to project rules rather than installing dependencies on Mac.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/options/optionChain.ts
git commit -m "Add option chain grouping utilities"
```

## Task 2: Replace Flat Option Table With Focused Chain Table

**Files:**

- Modify: `frontend/src/features/options/OptionChainTable.tsx`
- Test: TypeScript build in this task

- [ ] **Step 1: Replace the component implementation**

Replace `frontend/src/features/options/OptionChainTable.tsx` with this content:

```tsx
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
          <p>{underlying} · {expiry} · Call / Strike / Put</p>
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
                <th colSpan={7} className="side-title call-side">Call</th>
                <th className="strike-col">Strike</th>
                <th colSpan={7} className="side-title put-side">Put</th>
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
                <OptionRow
                  key={row.strike}
                  row={row}
                  selectedSymbol={selectedSymbol}
                  onSelect={setSelectedSymbol}
                />
              ))}
            </tbody>
          </table>
        </div>

        <aside className="selected-contract-panel">
          <h3>合约详情</h3>
          {selectedContract ? (
            <dl>
              <Detail label="合约" value={selectedContract.option_symbol} />
              <Detail label="Bid / Ask" value={`${formatOptionNumber(selectedContract.bid)} / ${formatOptionNumber(selectedContract.ask)}`} />
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
```

- [ ] **Step 2: Run the frontend build**

Run:

```bash
cd frontend
npm run build
```

Expected: build passes.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/options/OptionChainTable.tsx
git commit -m "Refine options chain table"
```

## Task 3: Add Focused Option-Chain Styles

**Files:**

- Modify: `frontend/src/app/App.css`
- Test: TypeScript build in this task

- [ ] **Step 1: Append option-chain styles**

Append this CSS to `frontend/src/app/App.css`:

```css
.option-header {
  align-items: center;
}

.option-toolbar {
  display: grid;
  grid-template-columns: minmax(140px, 180px) minmax(150px, 190px) minmax(280px, 1fr);
  gap: 12px;
  align-items: end;
  margin-bottom: 14px;
}

.option-toolbar label {
  display: grid;
  gap: 6px;
}

.option-toolbar span {
  color: #64748b;
  font-size: 12px;
}

.option-toolbar input,
.option-toolbar select {
  width: 100%;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 9px 10px;
  color: #172026;
  background: #ffffff;
}

.segmented-control {
  display: inline-flex;
  width: fit-content;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 3px;
  background: #f8fafc;
}

.segmented-control button {
  border: 0;
  border-radius: 6px;
  padding: 7px 10px;
  color: #475569;
  background: transparent;
}

.segmented-control button.active {
  color: #0f172a;
  background: #ffffff;
  box-shadow: 0 1px 2px rgb(15 23 42 / 0.08);
}

.option-chain-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 14px;
  align-items: start;
}

.option-chain-wrap {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.option-chain-table {
  min-width: 1160px;
  font-size: 12px;
}

.option-chain-table th,
.option-chain-table td {
  padding: 7px 8px;
  text-align: right;
  white-space: nowrap;
}

.option-chain-table th {
  position: sticky;
  top: 0;
  z-index: 1;
  color: #64748b;
  background: #f8fafc;
}

.side-title {
  text-align: center !important;
  font-weight: 760;
}

.call-side {
  color: #2563eb !important;
}

.put-side {
  color: #b45309 !important;
}

.strike-col {
  text-align: center !important;
  color: #0f172a;
  background: #f1f5f9 !important;
  font-weight: 760;
}

.atm-row td {
  background: #eff6ff;
}

.action-cell button {
  width: 100%;
  border: 0;
  padding: 0;
  color: #0f766e;
  background: transparent;
  font: inherit;
  font-weight: 700;
  text-align: right;
}

.action-cell button:hover,
.action-cell button:focus-visible {
  text-decoration: underline;
}

.selected-cell {
  color: #0f766e;
  background: #ecfdf5 !important;
  font-weight: 760;
}

.selected-contract-panel {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 14px;
  background: #f8fafc;
}

.selected-contract-panel h3 {
  margin: 0 0 12px;
  color: #0f172a;
  font-size: 15px;
}

.selected-contract-panel p {
  font-size: 13px;
}

.selected-contract-panel dl {
  display: grid;
  grid-template-columns: 86px minmax(0, 1fr);
  gap: 8px 10px;
  margin: 0;
  font-size: 12px;
}

.selected-contract-panel dt {
  color: #64748b;
}

.selected-contract-panel dd {
  min-width: 0;
  margin: 0;
  color: #0f172a;
  font-weight: 700;
  overflow-wrap: anywhere;
}

.empty-state {
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  padding: 16px;
  color: #64748b;
  background: #f8fafc;
}

@media (max-width: 1180px) {
  .option-chain-layout {
    grid-template-columns: 1fr;
  }

  .selected-contract-panel {
    max-width: none;
  }
}

@media (max-width: 760px) {
  .option-toolbar {
    grid-template-columns: 1fr;
  }

  .segmented-control {
    width: 100%;
  }

  .segmented-control button {
    flex: 1;
  }
}
```

- [ ] **Step 2: Run the frontend build**

Run:

```bash
cd frontend
npm run build
```

Expected: build passes.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/app/App.css
git commit -m "Style focused options chain UI"
```

## Task 4: Keep App Shell Focused and Non-Bloated

**Files:**

- Modify: `frontend/src/app/App.tsx`
- Test: TypeScript build in this task

- [ ] **Step 1: Update navigation labels only**

In `frontend/src/app/App.tsx`, replace the sidebar `<nav>` block with:

```tsx
<nav>
  <a href="#analysis">AI 分析</a>
  <a href="#report">研究报告</a>
  <a href="#market">行情数据</a>
  <a href="#options">期权链</a>
  <a href="#sync">数据同步</a>
</nav>
```

Do not add Dashboard, Runs, Settings, Learning, or Paper Trading links in this slice.

- [ ] **Step 2: Update topbar copy**

In the same file, keep the existing topbar structure but ensure the visible copy remains:

```tsx
<p className="eyebrow">AQuantLens US Options Branch</p>
<h2>美股与指数期权 AI 投研工作台</h2>
```

Keep the `Research Only` status pill.

- [ ] **Step 3: Run the frontend build**

Run:

```bash
cd frontend
npm run build
```

Expected: build passes.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/App.tsx
git commit -m "Keep US workbench navigation focused"
```

## Task 5: Final Verification

**Files:**

- Modify: none
- Test: `frontend` build and repository status

- [ ] **Step 1: Run frontend build**

Run:

```bash
cd frontend
npm run build
```

Expected: TypeScript and Vite production build pass.

- [ ] **Step 2: Check git status**

Run:

```bash
git status --short
```

Expected: no uncommitted changes after all task commits.

- [ ] **Step 3: Manual UI review**

If a dev server is available in the target environment, open the frontend and verify:

- Sidebar has only focused MVP links.
- The option panel still loads data through existing API callbacks.
- Moneyness buttons change visible rows.
- Clicking Bid, Ask, or Last shows contract details.
- Empty snapshot data shows a readiness-oriented message instead of looking broken.

Do not block this slice on Mac-local dev server startup if project rules require runtime verification on `ssh yasin-ubuntu`.

## Self-Review

Spec coverage:

- App shell focus: Task 4.
- Options page priority: Tasks 1, 2, and 3.
- Avoid copying AQuantLens mainline and bloat: scope guard plus Task 4.
- No broker/paper-trading/learning scope: scope guard.
- Real workflow over decorative dashboard: Dashboard intentionally deferred.

Placeholder scan:

- No TBD/TODO placeholders are present.
- No step says "add appropriate handling" without concrete code.

Type consistency:

- `MoneynessFilter`, `OptionChainRow`, and formatting functions are defined in Task 1 and imported in Task 2.
- All modified files use existing `OptionSnapshot` from `frontend/src/lib/api.ts`.
