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
