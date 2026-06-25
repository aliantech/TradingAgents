# Phase 13 SPY Mapping Provider Review

Status: Complete
Last Reviewed: 2026-06-23
Owner: Yasin

## Purpose

Repeat the guarded provider-backed `SPY` path after the real-runner report mapping improvement.

This verifies whether the persisted real-runner report now resolves the two prior review blockers:

- mapped trade plan was only a one-word final decision;
- options observation was placeholder-level.

## Execution

Ran in isolated Ubuntu copy:

```text
/tmp/tradingagents-phase13-mapping-review
```

The copy was synced from the Mac checkout. The Ubuntu runtime database was copied into the isolated backend directory so stored write-only provider readiness was available without printing secret values. The isolated database was explicitly set to:

```text
AQUANTLENS_TRADINGAGENTS_RUNNER_MODE=real-tradingagents
```

No main workspace database was modified.

## Preflight Probe

Command:

```bash
PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python \
  scripts/phase13_outcome_resolution_probe.py \
  --symbol SPY \
  --trade-date 2026-06-18 \
  --holding-days 1 \
  --benchmark SPY \
  --timeout-seconds 20
```

Result:

```json
{"actual_holding_days": 1, "alpha_return": 0.0, "benchmark": "SPY", "holding_days": 1, "raw_return": -0.0021627209678004686, "status": "succeeded", "symbol": "SPY", "timeout_seconds": 20, "trade_date": "2026-06-18", "yfinance_ticker_blocked": true}
```

## Guarded Smoke

Command:

```bash
PATH=/home/yasin/workspace/TradingAgents/backend/.venv/bin:$PATH \
  timeout 600 scripts/phase8_real_runner_smoke.sh SPY 2026-06-18 etf
```

Result:

```text
SMOKE_EXIT:0
STDOUT_BYTES:610
STDERR_BYTES:0
STDERR_FC_COUNT:0
```

Smoke JSON:

```json
{"symbol": "SPY", "status": "succeeded", "runner_mode": "real-tradingagents", "llm_provider": "openai", "model": "gpt-5.5", "missing": [], "progress": [{"step": "queued", "status": "completed", "message": "SPY 分析任务已进入队列。"}, {"step": "tradingagents", "status": "completed", "message": "真实 TradingAgents runner 执行完成。"}, {"step": "report", "status": "completed", "message": "真实 TradingAgents 输出已映射为中文研究报告。"}], "report_generated": true, "evidence_labels": ["tradingagents-real-runner", "direct-yahoo-chart-verified-snapshot"], "error_message": null}
```

## Persisted Provider-Backed Run

The first persisted attempt failed because the direct service path did not preload the stored provider key into the process environment. This was an execution-script issue, not a report-quality failure. The retry used the same `load_stored_provider_api_key()` bridge as the guarded smoke CLI without printing any secret values.

Successful analysis id:

```text
951e4aa5-c75e-4936-9ba9-e79f542c236d
```

Report id:

```text
a1029ec3-e74a-48b2-9f93-fc7750fb5f88
```

Run status:

```text
completed
```

Evidence labels:

```text
tradingagents-real-runner
direct-yahoo-chart-verified-snapshot
```

Confidence:

```text
0.5
```

## Mapping Checks

Result:

- Old trade wrapper present: `false`.
- Old options placeholder present: `false`.
- Markdown includes `## 研究计划`: `true`.
- Markdown includes `## 期权观察`: `true`.
- `trade_plan` includes observation conditions, invalidation conditions, risk boundaries, and follow-up review needs.
- `options_observation` includes IV, put/call skew, open interest, Gamma exposure, and event-volatility risk.
- Research-only language remains present.

## Data-Grounding Check

Result:

- Verified snapshot label is present.
- Report markdown includes one verified market-data snapshot.
- `746.74` appears in the report market/technical/markdown text.
- `549.33` does not appear in report market/technical/markdown text.
- No same-date close conflict was observed.
- The guarded smoke stderr was empty and `fc.yahoo.com` count was `0`.

## Review

Review id:

```text
b528ba45-8eb6-48a9-b646-ae7978e1c0e2
```

Scores:

| Dimension | Score |
| --- | ---: |
| Evidence clarity | 4 |
| Consistency | 4 |
| Risk coverage | 4 |
| Options relevance | 3 |
| Chinese readability | 4 |
| Research-only safety | 5 |

## Findings

Cleared blockers:

- The mapped trade plan is no longer a one-word final decision.
- The options observation is no longer placeholder text.
- The report still carries verified market snapshot evidence.
- The report remains research-only and does not generate automatic trading instructions.

Remaining blocker:

- The real runner still does not return a per-contract option chain. Options relevance improved, but this is still a risk-framework observation rather than contract-level options analysis.

## Decision

Do not automatically expand to `QQQ` yet.

The next decision is whether to accept this improved `SPY` review as sufficient for a guarded `QQQ` pilot, or first add per-contract option-chain context to the real-runner report mapping.

## Boundary

- No broker integration was added.
- No live execution was added.
- No live-trading UI control was added.
- No scheduled provider-backed research job was added.
- No automatic retry loop was added.
- No paper-to-live workflow was added.
- No secret values were read, printed, copied, or recorded.
