from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4


BarRow = dict[str, Any]
SignalRow = dict[str, Any]
JsonObject = dict[str, Any]

REQUIRED_BAR_COLUMNS = ("timestamp", "symbol", "close", "open", "high", "low", "volume")


@dataclass(frozen=True)
class SignalStrategy:
    strategy_id: str
    name: str
    description: str
    parameters: dict[str, Any]

    def generate_signals(self, bars: list[BarRow]) -> list[SignalRow]:
        validate_bars(bars)
        fast_window = int(self.parameters.get("fast_window", 2))
        slow_window = int(self.parameters.get("slow_window", 3))
        if fast_window <= 0 or slow_window <= 0:
            raise ValueError("moving average windows must be positive")
        if fast_window > slow_window:
            raise ValueError("fast_window must be less than or equal to slow_window")

        signals: list[SignalRow] = []
        position = 0
        closes = [float(row["close"]) for row in bars]
        for index, bar in enumerate(bars):
            signal = 0
            reason = "insufficient_window"
            if index + 1 >= slow_window:
                fast_ma = mean(closes[index + 1 - fast_window : index + 1])
                slow_ma = mean(closes[index + 1 - slow_window : index + 1])
                if position == 1 and float(bar["close"]) < fast_ma:
                    signal = -1
                    position = 0
                    reason = "fast_ma_below_slow_ma"
                elif fast_ma > slow_ma:
                    signal = 1 if position == 0 else 0
                    position = 1
                    reason = "fast_ma_above_slow_ma"
                elif fast_ma < slow_ma:
                    signal = -1 if position == 1 else 0
                    position = 0
                    reason = "fast_ma_below_slow_ma"
                else:
                    signal = 0
                    reason = "fast_ma_equals_slow_ma"
            signals.append(
                {
                    "timestamp": bar["timestamp"],
                    "symbol": bar["symbol"],
                    "close": float(bar["close"]),
                    "signal": signal,
                    "position": position,
                    "reason": reason,
                }
            )
        return signals


def validate_bars(bars: list[BarRow]) -> None:
    if not bars:
        raise ValueError("SignalStrategy requires at least one bar")
    for row in bars:
        for column in REQUIRED_BAR_COLUMNS:
            if column not in row:
                raise ValueError(f"missing required bar column: {column}")


def run_deterministic_backtest(signals: list[SignalRow], *, initial_equity: float) -> JsonObject:
    if initial_equity <= 0:
        raise ValueError("initial_equity must be positive")

    equity = float(initial_equity)
    open_trade: SignalRow | None = None
    trades: list[JsonObject] = []
    for row in signals:
        signal = int(row["signal"])
        if signal == 1 and open_trade is None:
            open_trade = row
        elif signal == -1 and open_trade is not None:
            pnl = round(float(row["close"]) - float(open_trade["close"]), 4)
            equity = round(equity + pnl, 4)
            trades.append(
                {
                    "entry_timestamp": open_trade["timestamp"],
                    "exit_timestamp": row["timestamp"],
                    "symbol": row["symbol"],
                    "entry_price": float(open_trade["close"]),
                    "exit_price": float(row["close"]),
                    "quantity": 1,
                    "pnl": pnl,
                }
            )
            open_trade = None

    return {
        "mode": "research_only",
        "initial_equity": normalize_number(initial_equity),
        "final_equity": normalize_number(equity),
        "return_pct": round(((equity - initial_equity) / initial_equity) * 100, 4),
        "trades": trades,
    }


def build_chart_overlay(symbol: str, signals: list[SignalRow]) -> JsonObject:
    return {
        "symbol": symbol,
        "price_series": [
            {
                "time": row["timestamp"],
                "value": float(row["close"]),
            }
            for row in signals
        ],
        "markers": [
            marker
            for row in signals
            if (marker := signal_marker(row)) is not None
        ],
    }


def signal_marker(row: SignalRow) -> JsonObject | None:
    signal = int(row["signal"])
    if signal == 1:
        return {
            "time": row["timestamp"],
            "position": "belowBar",
            "color": "#16a34a",
            "shape": "arrowUp",
            "text": "SignalStrategy buy",
        }
    if signal == -1:
        return {
            "time": row["timestamp"],
            "position": "aboveBar",
            "color": "#dc2626",
            "shape": "arrowDown",
            "text": "SignalStrategy exit",
        }
    return None


def create_report_linked_note(
    *,
    report_id: UUID,
    strategy_id: str,
    symbol: str,
    title: str,
    body: str,
    evidence_labels: list[str],
) -> JsonObject:
    return {
        "note_id": str(uuid4()),
        "report_id": str(report_id),
        "strategy_id": strategy_id,
        "symbol": symbol,
        "title": title,
        "body": body,
        "evidence_labels": list(evidence_labels),
        "scope": "research_note",
    }


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def normalize_number(value: float) -> int | float:
    if float(value).is_integer():
        return int(value)
    return round(float(value), 4)
