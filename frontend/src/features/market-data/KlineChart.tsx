import { useEffect, useMemo, useRef } from "react";
import { useTranslation } from "react-i18next";
import {
  CandlestickSeries,
  ColorType,
  createChart,
  HistogramSeries,
  LineSeries,
  type CandlestickData,
  type HistogramData,
  type IChartApi,
  type LineData,
  type Time,
} from "lightweight-charts";

import type { MarketBar } from "../../lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type KlineChartProps = {
  bars: MarketBar[];
};

const MARKET_COLORS = {
  up: "#16a34a",
  down: "#dc2626",
  upVolume: "rgba(22, 163, 74, 0.32)",
  downVolume: "rgba(220, 38, 38, 0.32)",
  text: "#64748b",
  grid: "#e2e8f0",
  sma20: "#2563eb",
  sma50: "#7c3aed",
};

export function KlineChart({ bars }: KlineChartProps) {
  const { t } = useTranslation();
  const chartContainerRef = useRef<HTMLDivElement | null>(null);
  const data = useMemo(() => toCandlestickData(bars), [bars]);

  useEffect(() => {
    const container = chartContainerRef.current;
    if (!container || data.length === 0) return;
    const volumeData = toVolumeData(bars, MARKET_COLORS.upVolume, MARKET_COLORS.downVolume);
    const sma20 = toMovingAverageData(data, 20);
    const sma50 = toMovingAverageData(data, 50);

    const chart: IChartApi = createChart(container, {
      autoSize: true,
      height: 320,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: MARKET_COLORS.text,
      },
      grid: {
        horzLines: { color: MARKET_COLORS.grid },
        vertLines: { color: MARKET_COLORS.grid },
      },
      rightPriceScale: {
        borderColor: MARKET_COLORS.grid,
      },
      timeScale: {
        borderColor: MARKET_COLORS.grid,
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: {
        mode: 1,
      },
    });

    const series = chart.addSeries(CandlestickSeries, {
      upColor: MARKET_COLORS.up,
      downColor: MARKET_COLORS.down,
      borderUpColor: MARKET_COLORS.up,
      borderDownColor: MARKET_COLORS.down,
      wickUpColor: MARKET_COLORS.up,
      wickDownColor: MARKET_COLORS.down,
    });
    series.setData(data);
    const sma20Series = chart.addSeries(LineSeries, {
      color: MARKET_COLORS.sma20,
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
      title: "SMA20",
    });
    sma20Series.setData(sma20);
    const sma50Series = chart.addSeries(LineSeries, {
      color: MARKET_COLORS.sma50,
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
      title: "SMA50",
    });
    sma50Series.setData(sma50);
    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: MARKET_COLORS.text,
      priceFormat: {
        type: "volume",
      },
      priceScaleId: "volume",
    });
    volumeSeries.setData(volumeData);
    chart.priceScale("volume").applyOptions({
      scaleMargins: {
        top: 0.78,
        bottom: 0,
      },
    });
    chart.timeScale().fitContent();

    return () => {
      chart.remove();
    };
  }, [bars, data]);

  if (!bars.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{t("market.chartTitle")}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{t("market.chartEmpty")}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{t("market.chartTitle")}</CardTitle>
      </CardHeader>
      <CardContent>
        <div ref={chartContainerRef} className="h-80 min-w-0" aria-label={`${bars[0].symbol} candlestick chart`} />
      </CardContent>
    </Card>
  );
}

function toCandlestickData(bars: MarketBar[]): CandlestickData<Time>[] {
  const byTime = new Map<number, CandlestickData<Time>>();
  for (const bar of bars) {
    const time = Math.floor(new Date(bar.timestamp).getTime() / 1000);
    byTime.set(time, {
      time: time as Time,
      open: bar.open,
      high: bar.high,
      low: bar.low,
      close: bar.close,
    });
  }
  return Array.from(byTime.values()).sort((left, right) => Number(left.time) - Number(right.time));
}

function toVolumeData(bars: MarketBar[], upColor: string, downColor: string): HistogramData<Time>[] {
  const byTime = new Map<number, HistogramData<Time>>();
  for (const bar of bars) {
    const time = Math.floor(new Date(bar.timestamp).getTime() / 1000);
    byTime.set(time, {
      time: time as Time,
      value: bar.volume,
      color: bar.close >= bar.open ? upColor : downColor,
    });
  }
  return Array.from(byTime.values()).sort((left, right) => Number(left.time) - Number(right.time));
}

function toMovingAverageData(data: CandlestickData<Time>[], period: number): LineData<Time>[] {
  return data
    .map((bar, index) => {
      if (index + 1 < period) return null;
      const window = data.slice(index + 1 - period, index + 1);
      const value = window.reduce((sum, item) => sum + item.close, 0) / period;
      return {
        time: bar.time,
        value,
      };
    })
    .filter((item): item is LineData<Time> => item !== null);
}
