#!/usr/bin/env python3
"""Bounded non-LLM probe for TradingAgents outcome-resolution returns."""

from __future__ import annotations

import argparse
import json
import signal
from typing import Any

import yfinance

from tradingagents.graph.trading_graph import TradingAgentsGraph


class OutcomeProbeTimeout(TimeoutError):
    pass


class YFinanceTickerBlocked(RuntimeError):
    pass


def run_probe(
    symbol: str,
    trade_date: str,
    *,
    holding_days: int,
    benchmark: str,
    timeout_seconds: int,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "symbol": symbol.upper(),
        "trade_date": trade_date,
        "holding_days": holding_days,
        "benchmark": benchmark,
        "timeout_seconds": timeout_seconds,
        "yfinance_ticker_blocked": True,
    }

    original_ticker = yfinance.Ticker
    previous_handler = signal.getsignal(signal.SIGALRM)
    blocked_calls = []

    def blocked_yfinance_ticker(*args, **kwargs):
        blocked_calls.append(True)
        return _blocked_yfinance_ticker(*args, **kwargs)

    yfinance.Ticker = blocked_yfinance_ticker
    signal.signal(signal.SIGALRM, _raise_timeout)
    signal.setitimer(signal.ITIMER_REAL, timeout_seconds)
    try:
        raw_return, alpha_return, actual_days = TradingAgentsGraph._fetch_returns(
            None,
            symbol,
            trade_date,
            holding_days=holding_days,
            benchmark=benchmark,
        )
    except OutcomeProbeTimeout as error:
        payload.update({"status": "timeout", "error_type": type(error).__name__, "error_message": str(error)})
        return payload
    except Exception as error:  # noqa: BLE001 - probe must report sanitized failure as JSON
        payload.update({"status": "failed", "error_type": type(error).__name__, "error_message": str(error)})
        return payload
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        yfinance.Ticker = original_ticker

    payload.update(
        {
            "raw_return": raw_return,
            "alpha_return": alpha_return,
            "actual_holding_days": actual_days,
            "status": "succeeded" if raw_return is not None else "no_data",
        }
    )
    if blocked_calls:
        payload.update(
            {
                "status": "failed",
                "error_type": YFinanceTickerBlocked.__name__,
                "error_message": "yfinance.Ticker is disabled in the Phase 13 outcome-resolution probe.",
            }
        )
    return payload


def _blocked_yfinance_ticker(*_args, **_kwargs):
    raise YFinanceTickerBlocked("yfinance.Ticker is disabled in the Phase 13 outcome-resolution probe.")


def _raise_timeout(_signum, _frame):
    raise OutcomeProbeTimeout("Outcome-resolution probe timed out.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", default="SPY")
    parser.add_argument("--trade-date", default="2026-06-18")
    parser.add_argument("--holding-days", type=int, default=1)
    parser.add_argument("--benchmark", default="SPY")
    parser.add_argument("--timeout-seconds", type=int, default=20)
    args = parser.parse_args(argv)

    result = run_probe(
        args.symbol,
        args.trade_date,
        holding_days=args.holding_days,
        benchmark=args.benchmark,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if result["status"] == "succeeded":
        return 0
    if result["status"] == "no_data":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
