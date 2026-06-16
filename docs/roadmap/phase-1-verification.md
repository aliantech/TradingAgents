# Phase 1 Verification

## Required End-to-End Flow

- Start backend API.
- Start frontend UI.
- Open AQuantLens workbench.
- Select Chinese UI.
- Start SPY analysis.
- Confirm analysis job enters queued/running status.
- Confirm progress updates render in UI.
- Confirm Chinese report is generated.
- Confirm report is saved.
- Confirm report appears in history.
- Confirm SPY K-line chart renders.
- Confirm selected SPY or SPX option-chain snapshot renders.

## Safety Checks

- No live order placement exists.
- No broker credentials are required for Phase 1.
- No `.env` values are printed in logs.
- AI output is labelled as research, not investment advice.
