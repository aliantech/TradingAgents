CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS instruments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol text NOT NULL,
  asset_type text NOT NULL CHECK (asset_type IN ('equity', 'etf', 'index', 'option', 'future', 'crypto')),
  exchange text NOT NULL,
  currency text NOT NULL DEFAULT 'USD',
  timezone text NOT NULL DEFAULT 'America/New_York',
  name text,
  source text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (symbol, asset_type, exchange)
);

CREATE TABLE IF NOT EXISTS option_contracts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  underlying_instrument_id uuid NOT NULL REFERENCES instruments(id),
  option_symbol text NOT NULL UNIQUE,
  expiry_date date NOT NULL,
  strike numeric(18, 6) NOT NULL,
  right text NOT NULL CHECK (right IN ('call', 'put')),
  exercise_style text NOT NULL DEFAULT 'unknown',
  multiplier integer NOT NULL DEFAULT 100,
  settlement_type text NOT NULL DEFAULT 'unknown',
  source text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS market_bars (
  instrument_id uuid NOT NULL REFERENCES instruments(id),
  timeframe text NOT NULL CHECK (timeframe IN ('1m', '5m', '1d')),
  timestamp timestamptz NOT NULL,
  open numeric(18, 6) NOT NULL,
  high numeric(18, 6) NOT NULL,
  low numeric(18, 6) NOT NULL,
  close numeric(18, 6) NOT NULL,
  volume bigint NOT NULL DEFAULT 0,
  vwap numeric(18, 6),
  source text NOT NULL,
  inserted_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (instrument_id, timeframe, timestamp, source)
);

SELECT create_hypertable('market_bars', 'timestamp', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS option_snapshots (
  contract_id uuid NOT NULL REFERENCES option_contracts(id),
  timestamp timestamptz NOT NULL,
  bid numeric(18, 6),
  ask numeric(18, 6),
  last numeric(18, 6),
  bid_size integer,
  ask_size integer,
  volume bigint NOT NULL DEFAULT 0,
  open_interest bigint,
  implied_volatility numeric(18, 8),
  delta numeric(18, 8),
  gamma numeric(18, 8),
  theta numeric(18, 8),
  vega numeric(18, 8),
  rho numeric(18, 8),
  source text NOT NULL,
  inserted_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (contract_id, timestamp, source)
);

SELECT create_hypertable('option_snapshots', 'timestamp', if_not_exists => TRUE);

CREATE TABLE IF NOT EXISTS analysis_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  symbol text NOT NULL,
  asset_type text NOT NULL,
  analysis_date date NOT NULL,
  language text NOT NULL DEFAULT 'zh',
  llm_provider text NOT NULL,
  model text NOT NULL,
  depth text NOT NULL,
  status text NOT NULL,
  progress jsonb NOT NULL DEFAULT '[]'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS analysis_reports (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  analysis_run_id uuid NOT NULL REFERENCES analysis_runs(id),
  symbol text NOT NULL,
  language text NOT NULL DEFAULT 'zh',
  markdown text NOT NULL,
  report_json jsonb NOT NULL,
  confidence numeric(5, 4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS provider_sync_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  provider text NOT NULL,
  sync_type text NOT NULL,
  status text NOT NULL,
  started_at timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz,
  rows_written integer NOT NULL DEFAULT 0,
  error_message text
);

CREATE INDEX IF NOT EXISTS idx_instruments_symbol ON instruments(symbol);
CREATE INDEX IF NOT EXISTS idx_option_contracts_underlying_expiry ON option_contracts(underlying_instrument_id, expiry_date);
CREATE INDEX IF NOT EXISTS idx_analysis_reports_symbol_created ON analysis_reports(symbol, created_at DESC);
