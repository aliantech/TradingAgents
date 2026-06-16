import type { OptionSnapshot } from "../../lib/api";

type OptionChainTableProps = {
  snapshots: OptionSnapshot[];
};

export function OptionChainTable({ snapshots }: OptionChainTableProps) {
  return (
    <section className="panel option-panel">
      <div className="panel-header">
        <div>
          <h2>期权链</h2>
          <p>SPX/SPY/QQQ 与部分高流动性美股期权的 Greeks 和 IV 视图。</p>
        </div>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>合约</th>
              <th>Bid</th>
              <th>Ask</th>
              <th>IV</th>
              <th>Delta</th>
              <th>Theta</th>
              <th>OI</th>
            </tr>
          </thead>
          <tbody>
            {snapshots.map((snapshot) => (
              <tr key={snapshot.option_symbol}>
                <td>{snapshot.option_symbol}</td>
                <td>{snapshot.bid?.toFixed(2)}</td>
                <td>{snapshot.ask?.toFixed(2)}</td>
                <td>{snapshot.implied_volatility ? `${(snapshot.implied_volatility * 100).toFixed(1)}%` : "-"}</td>
                <td>{snapshot.delta?.toFixed(2)}</td>
                <td>{snapshot.theta?.toFixed(2)}</td>
                <td>{snapshot.open_interest?.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
