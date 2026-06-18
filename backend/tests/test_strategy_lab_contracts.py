from uuid import UUID, uuid4

import pytest

from app.strategy_lab.contracts import (
    SignalStrategy,
    build_chart_overlay,
    create_report_linked_note,
    run_deterministic_backtest,
)


def test_signal_strategy_generates_dataframe_signal_contract():
    strategy = SignalStrategy(
        strategy_id="ma-cross-research",
        name="MA Cross Research",
        description="Research-only moving average signal contract.",
        parameters={"fast_window": 2, "slow_window": 3},
    )

    signals = strategy.generate_signals(sample_bars())

    assert signals == [
        {
            "timestamp": "2026-06-19T13:30:00Z",
            "symbol": "SPY",
            "close": 100.0,
            "signal": 0,
            "position": 0,
            "reason": "insufficient_window",
        },
        {
            "timestamp": "2026-06-19T13:31:00Z",
            "symbol": "SPY",
            "close": 102.0,
            "signal": 0,
            "position": 0,
            "reason": "insufficient_window",
        },
        {
            "timestamp": "2026-06-19T13:32:00Z",
            "symbol": "SPY",
            "close": 104.0,
            "signal": 1,
            "position": 1,
            "reason": "fast_ma_above_slow_ma",
        },
        {
            "timestamp": "2026-06-19T13:33:00Z",
            "symbol": "SPY",
            "close": 101.0,
            "signal": -1,
            "position": 0,
            "reason": "fast_ma_below_slow_ma",
        },
    ]


def test_signal_strategy_requires_dataframe_columns():
    strategy = SignalStrategy(
        strategy_id="ma-cross-research",
        name="MA Cross Research",
        description="Research-only moving average signal contract.",
        parameters={"fast_window": 2, "slow_window": 3},
    )

    with pytest.raises(ValueError, match="missing required bar column: close"):
        strategy.generate_signals([{"timestamp": "2026-06-19T13:30:00Z", "symbol": "SPY"}])


def test_deterministic_backtest_contract_is_repeatable_and_research_only():
    strategy = SignalStrategy(
        strategy_id="ma-cross-research",
        name="MA Cross Research",
        description="Research-only moving average signal contract.",
        parameters={"fast_window": 2, "slow_window": 3},
    )
    signals = strategy.generate_signals(sample_bars())

    first_result = run_deterministic_backtest(signals, initial_equity=10_000)
    second_result = run_deterministic_backtest(signals, initial_equity=10_000)

    assert first_result == second_result
    assert first_result["mode"] == "research_only"
    assert first_result["initial_equity"] == 10_000
    assert first_result["final_equity"] == 9_997.0
    assert first_result["return_pct"] == -0.03
    assert first_result["trades"] == [
        {
            "entry_timestamp": "2026-06-19T13:32:00Z",
            "exit_timestamp": "2026-06-19T13:33:00Z",
            "symbol": "SPY",
            "entry_price": 104.0,
            "exit_price": 101.0,
            "quantity": 1,
            "pnl": -3.0,
        }
    ]
    assert not any("broker" in key or "order" in key for key in first_result)


def test_chart_overlay_contract_maps_signals_to_markers():
    strategy = SignalStrategy(
        strategy_id="ma-cross-research",
        name="MA Cross Research",
        description="Research-only moving average signal contract.",
        parameters={"fast_window": 2, "slow_window": 3},
    )
    signals = strategy.generate_signals(sample_bars())

    overlay = build_chart_overlay("SPY", signals)

    assert overlay == {
        "symbol": "SPY",
        "price_series": [
            {"time": "2026-06-19T13:30:00Z", "value": 100.0},
            {"time": "2026-06-19T13:31:00Z", "value": 102.0},
            {"time": "2026-06-19T13:32:00Z", "value": 104.0},
            {"time": "2026-06-19T13:33:00Z", "value": 101.0},
        ],
        "markers": [
            {
                "time": "2026-06-19T13:32:00Z",
                "position": "belowBar",
                "color": "#16a34a",
                "shape": "arrowUp",
                "text": "SignalStrategy buy",
            },
            {
                "time": "2026-06-19T13:33:00Z",
                "position": "aboveBar",
                "color": "#dc2626",
                "shape": "arrowDown",
                "text": "SignalStrategy exit",
            },
        ],
    }


def test_report_linked_note_contract_keeps_strategy_research_scoped():
    report_id = uuid4()

    note = create_report_linked_note(
        report_id=report_id,
        strategy_id="ma-cross-research",
        symbol="SPY",
        title="MA cross follow-up",
        body="Signal turned defensive near the final bar.",
        evidence_labels=["market-bars", "technical-setup"],
    )

    assert note == {
        "note_id": str(UUID(note["note_id"])),
        "report_id": str(report_id),
        "strategy_id": "ma-cross-research",
        "symbol": "SPY",
        "title": "MA cross follow-up",
        "body": "Signal turned defensive near the final bar.",
        "evidence_labels": ["market-bars", "technical-setup"],
        "scope": "research_note",
    }
    assert "order" not in str(note).lower()
    assert "broker" not in str(note).lower()


def sample_bars():
    return [
        {
            "timestamp": "2026-06-19T13:30:00Z",
            "symbol": "SPY",
            "open": 99.0,
            "high": 101.0,
            "low": 98.5,
            "close": 100.0,
            "volume": 1000,
        },
        {
            "timestamp": "2026-06-19T13:31:00Z",
            "symbol": "SPY",
            "open": 100.0,
            "high": 103.0,
            "low": 99.5,
            "close": 102.0,
            "volume": 1100,
        },
        {
            "timestamp": "2026-06-19T13:32:00Z",
            "symbol": "SPY",
            "open": 102.0,
            "high": 105.0,
            "low": 101.5,
            "close": 104.0,
            "volume": 1200,
        },
        {
            "timestamp": "2026-06-19T13:33:00Z",
            "symbol": "SPY",
            "open": 104.0,
            "high": 104.5,
            "low": 100.0,
            "close": 101.0,
            "volume": 1300,
        },
    ]
