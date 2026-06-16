import type { MarketBar } from "../../lib/api";

type KlineChartProps = {
  bars: MarketBar[];
};

export function KlineChart({ bars }: KlineChartProps) {
  if (!bars.length) {
    return (
      <section className="panel chart-panel">
        <h2>K 线图</h2>
        <p className="empty">等待行情数据。</p>
      </section>
    );
  }

  const width = 680;
  const height = 260;
  const padding = 24;
  const highs = bars.map((bar) => bar.high);
  const lows = bars.map((bar) => bar.low);
  const max = Math.max(...highs);
  const min = Math.min(...lows);
  const span = max - min || 1;
  const candleWidth = Math.max(10, (width - padding * 2) / bars.length - 10);

  const y = (price: number) => padding + ((max - price) / span) * (height - padding * 2);
  const x = (index: number) => padding + index * ((width - padding * 2) / Math.max(1, bars.length - 1));

  return (
    <section className="panel chart-panel">
      <div className="panel-header">
        <div>
          <h2>K 线图</h2>
          <p>{bars[0].symbol} · 1m · sample</p>
        </div>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="SPY K line chart">
        <line x1={padding} y1={padding} x2={padding} y2={height - padding} className="axis" />
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} className="axis" />
        {bars.map((bar, index) => {
          const center = x(index);
          const up = bar.close >= bar.open;
          const bodyTop = y(Math.max(bar.open, bar.close));
          const bodyHeight = Math.max(3, Math.abs(y(bar.open) - y(bar.close)));
          return (
            <g key={bar.timestamp}>
              <line x1={center} y1={y(bar.high)} x2={center} y2={y(bar.low)} className={up ? "candle-up" : "candle-down"} />
              <rect
                x={center - candleWidth / 2}
                y={bodyTop}
                width={candleWidth}
                height={bodyHeight}
                className={up ? "candle-up-fill" : "candle-down-fill"}
              />
            </g>
          );
        })}
      </svg>
    </section>
  );
}
