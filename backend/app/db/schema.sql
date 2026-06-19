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
  analyst_set text NOT NULL DEFAULT 'macro-options',
  research_template text NOT NULL DEFAULT 'general',
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
  target_symbol text,
  target_expiry date,
  status text NOT NULL,
  started_at timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz,
  rows_written integer NOT NULL DEFAULT 0,
  error_message text
);

CREATE TABLE IF NOT EXISTS app_settings (
  key text PRIMARY KEY,
  value text NOT NULL DEFAULT '',
  category text NOT NULL DEFAULT 'general',
  is_secret boolean NOT NULL DEFAULT false,
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agent_tokens (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  token_prefix text NOT NULL,
  token_hash text NOT NULL UNIQUE,
  scopes text NOT NULL DEFAULT 'R',
  markets text NOT NULL DEFAULT 'US',
  instruments text NOT NULL DEFAULT '*',
  rate_limit_per_min integer NOT NULL DEFAULT 60,
  status text NOT NULL DEFAULT 'active',
  expires_at timestamptz,
  last_used_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agent_audit (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_token_id uuid REFERENCES agent_tokens(id),
  agent_name text,
  route text NOT NULL,
  method text NOT NULL,
  scope_class text NOT NULL DEFAULT 'R',
  status_code integer NOT NULL,
  detail text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS agent_jobs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_token_id uuid NOT NULL REFERENCES agent_tokens(id),
  agent_name text NOT NULL,
  job_type text NOT NULL,
  idempotency_key text,
  status text NOT NULL,
  request_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  progress jsonb NOT NULL DEFAULT '[]'::jsonb,
  result_json jsonb,
  error_message text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz,
  CONSTRAINT uq_agent_jobs_token_type_idempotency UNIQUE (agent_token_id, job_type, idempotency_key)
);

CREATE TABLE IF NOT EXISTS strategy_experiments (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  title text NOT NULL,
  symbol text NOT NULL,
  strategy_id text NOT NULL,
  scope text NOT NULL DEFAULT 'research_only',
  parameters jsonb NOT NULL DEFAULT '{}'::jsonb,
  preview_json jsonb NOT NULL DEFAULT '{}'::jsonb,
  tags jsonb NOT NULL DEFAULT '[]'::jsonb,
  notes text,
  archived boolean NOT NULL DEFAULT false,
  review_status text NOT NULL DEFAULT 'draft',
  review_checklist jsonb NOT NULL DEFAULT '{}'::jsonb,
  report_id uuid REFERENCES analysis_reports(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS paper_accounts (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  base_currency text NOT NULL DEFAULT 'USD',
  starting_cash numeric(18, 6) NOT NULL,
  current_cash numeric(18, 6) NOT NULL,
  status text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS paper_order_intents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id uuid NOT NULL REFERENCES paper_accounts(id),
  source text NOT NULL,
  source_reference_id uuid NOT NULL,
  symbol text NOT NULL,
  asset_class text NOT NULL,
  side text NOT NULL,
  quantity numeric(18, 6) NOT NULL,
  order_type text NOT NULL,
  limit_price numeric(18, 6),
  time_in_force text NOT NULL,
  status text NOT NULL,
  idempotency_key text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_paper_intents_account_idempotency UNIQUE (account_id, idempotency_key)
);

CREATE TABLE IF NOT EXISTS paper_risk_decisions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  intent_id uuid NOT NULL REFERENCES paper_order_intents(id),
  result text NOT NULL,
  reason_codes jsonb NOT NULL DEFAULT '[]'::jsonb,
  explanation text NOT NULL,
  estimated_notional numeric(18, 6) NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS paper_fills (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  intent_id uuid NOT NULL REFERENCES paper_order_intents(id),
  account_id uuid NOT NULL REFERENCES paper_accounts(id),
  symbol text NOT NULL,
  asset_class text NOT NULL,
  side text NOT NULL,
  quantity numeric(18, 6) NOT NULL,
  fill_price numeric(18, 6) NOT NULL,
  filled_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS paper_positions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  account_id uuid NOT NULL REFERENCES paper_accounts(id),
  symbol text NOT NULL,
  asset_class text NOT NULL,
  quantity numeric(18, 6) NOT NULL,
  average_price numeric(18, 6) NOT NULL,
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT uq_paper_positions_account_symbol_asset UNIQUE (account_id, symbol, asset_class)
);

CREATE TABLE IF NOT EXISTS paper_audit_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_type text NOT NULL,
  resource_type text NOT NULL,
  resource_id uuid NOT NULL,
  action text NOT NULL,
  outcome text NOT NULL,
  reason_code text NOT NULL,
  message text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_instruments_symbol ON instruments(symbol);
CREATE INDEX IF NOT EXISTS idx_option_contracts_underlying_expiry ON option_contracts(underlying_instrument_id, expiry_date);
CREATE INDEX IF NOT EXISTS idx_analysis_reports_symbol_created ON analysis_reports(symbol, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_tokens_hash ON agent_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_agent_audit_route ON agent_audit(route, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_jobs_token_created ON agent_jobs(agent_token_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_strategy_experiments_symbol_created ON strategy_experiments(symbol, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_strategy_experiments_archived ON strategy_experiments(archived);
CREATE INDEX IF NOT EXISTS idx_strategy_experiments_review_status ON strategy_experiments(review_status);
CREATE INDEX IF NOT EXISTS idx_paper_accounts_status ON paper_accounts(status);
CREATE INDEX IF NOT EXISTS idx_paper_order_intents_account_created ON paper_order_intents(account_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_paper_order_intents_status ON paper_order_intents(status);
CREATE INDEX IF NOT EXISTS idx_paper_risk_decisions_intent_created ON paper_risk_decisions(intent_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_paper_fills_intent_filled ON paper_fills(intent_id, filled_at ASC);
CREATE INDEX IF NOT EXISTS idx_paper_positions_account_symbol ON paper_positions(account_id, symbol);
CREATE INDEX IF NOT EXISTS idx_paper_audit_events_resource_created ON paper_audit_events(resource_id, created_at ASC);
