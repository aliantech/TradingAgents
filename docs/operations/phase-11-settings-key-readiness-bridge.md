# Phase 11 Settings Key Readiness Bridge

Status: Complete
Last Reviewed: 2026-06-20
Owner: Yasin

## Purpose

This record captures the Phase 11 fix that lets the guarded real-runner smoke use write-only LLM provider keys saved through Settings.

The frontend Settings path can save `OPENAI_API_KEY` as a secret and mask it on readback, but the previous smoke CLI only checked process environment variables. This created a mismatch: Settings showed the key as saved while the smoke guard still returned `not_ready`.

## Change

- `backend/app/analysis/cli.py` now loads the selected provider key from `SettingsRepository` into the current smoke process environment when the process environment does not already provide it.
- The key value is not printed, returned, logged, or written to docs.
- Existing process environment variables take precedence over stored Settings values.
- Unknown provider mappings still fail readiness by variable name only.

## Sanitized Runtime Checks

Masked Settings API readback:

```json
{
  "settings_api_reachable": true,
  "openai_key_item_present": true,
  "openai_key_has_value": true,
  "openai_key_value_returned": false
}
```

Readiness after the bridge and explicit runtime gate:

```json
{
  "status": "ready",
  "runner_mode": "real-tradingagents",
  "llm_provider": "openai",
  "deep_model": "gpt-5.5",
  "quick_model": "gpt-5.4-mini",
  "missing": [],
  "settings_secret_loaded_for_process": true
}
```

## Verification

Focused tests passed in isolated Ubuntu temp copy `/tmp/tradingagents-phase11-settings-key-fix-22ccJZ`:

```bash
cd /tmp/tradingagents-phase11-settings-key-fix-22ccJZ/backend
PYTHONPATH=. /home/yasin/workspace/TradingAgents/backend/.venv/bin/python -m pytest \
  tests/test_analysis_cli_real_runner_smoke.py \
  tests/test_phase8_real_runner_smoke_script.py \
  tests/test_settings_api.py \
  -q
```

Result: 10 passed.

## Boundary

- No `.env` file was sourced.
- No secret value was printed, returned, copied, pasted, stored in docs, or committed.
- No broker integration, live execution, scheduled job, automatic retry, or paper-to-live workflow was added.
