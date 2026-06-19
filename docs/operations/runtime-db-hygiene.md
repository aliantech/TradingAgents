# Runtime DB Hygiene

This branch keeps the local runtime database for real AQuantLens workbench state only.

## Test Isolation

`backend/tests/conftest.py` forces pytest to use a temporary SQLite database by default. Tests must not write to:

```text
backend/aquantlens_us.db
```

If a test process connects to the runtime DB, the autouse guard fails the test. Only an explicit manual smoke run may opt out:

```bash
AQUANTLENS_ALLOW_RUNTIME_DB_TESTS=1 pytest ...
```

Use that opt-out sparingly and only when intentionally validating the running local database.

## Cleanup Script

Use the cleanup script when historical mock, sample, or test audit rows appear in the runtime task center.

Dry run:

```bash
scripts/cleanup_runtime_db.py
```

Execute with automatic SQLite backup:

```bash
scripts/cleanup_runtime_db.py --execute
```

The script removes:

- legacy mock reports and their analysis runs
- analysis runs without reports, unless `--keep-failed-analysis` is passed
- `sample`, `fixture`, `future`, and `unit-test-provider*` sync audit rows
- legacy Polygon options audit rows missing `target_symbol` or `target_expiry`
- provider sync audit rows before `2026-06-19`, unless `--keep-pre-2026-06-19-sync` is passed

The script does not remove market bars, option contracts, option snapshots, settings, or credentials.

## Task Center Display

The frontend task center defaults to product data:

- provider filter defaults to `polygon`
- sample, fixture, future, and unit-test providers are hidden
- analysis and sync tables render bounded, scrollable recent slices
- option-chain audit rows display target symbol and expiry, for example `QQQ · 2026-06-26`

This keeps operational screens from turning into raw test logs.
