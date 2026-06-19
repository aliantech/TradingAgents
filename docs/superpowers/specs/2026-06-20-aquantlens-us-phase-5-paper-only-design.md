# AQuantLens US Phase 5 Paper-Only Design

## Status

Status: Draft for review
Last Reviewed: 2026-06-20
Owner: Yasin

## Purpose

Phase 5 introduces the architecture for paper-only execution in the TradingAgents-based AQuantLens US/options branch.

The design bridges Phase 4 research candidates and future simulated trading workflows without weakening the branch boundary. It does not authorize live broker execution, broker credential handling, or AI-directed live trading.

## Assumptions

- Phase 4 candidate status means research review candidate only.
- Phase 5 starts with paper architecture and safety contracts before implementation.
- Paper execution is simulated inside AQuantLens and must not call broker APIs.
- Runtime state must be database-backed.
- Human approval is required before a reviewed research candidate becomes a paper intent.
- Live execution requires a separate future decision and separate safety design.

## Recommended Approach

Use an intent-first paper workflow:

```text
Candidate Experiment
-> Paper Order Intent Draft
-> RiskGuard Decision
-> Human Review
-> PaperExecutionAdapter
-> Paper Fill
-> Paper Position
-> Audit Trail
```

This approach keeps paper simulation inspectable, testable, and reversible at the workflow level. It also prevents Strategy Lab candidates, agents, or MCP tools from becoming direct order-placement surfaces.

## Architecture

### Paper Domain Layer

The paper domain layer owns typed contracts for:

- Paper account.
- Order intent.
- Risk decision.
- Paper fill.
- Paper position.
- Trading-class audit event.

These contracts should be independent from FastAPI route handlers and frontend presentation code. The first implementation slice should test them as plain Python objects or Pydantic schemas before adding persistence.

### RiskGuard Layer

RiskGuard is a pure validation layer. It receives an order intent plus account and market metadata, then returns a pass or reject decision with reason codes.

RiskGuard does not mutate positions, submit fills, or call brokers. It exists so every later write path can be tested against the same safety rules.

### Persistence Layer

Paper state must be stored through SQLAlchemy models and the project database session pattern.

Persisted records should include:

- Paper accounts.
- Order intents.
- Risk decisions.
- Paper fills.
- Paper positions.
- Append-only audit events.

Production paper state must not use JSON files, static configuration, or process memory.

### API Layer

The API should expose paper intent and review workflows only after the domain and RiskGuard layers are tested.

Initial API actions:

- Create draft paper intent.
- Run RiskGuard.
- List paper intents.
- Read paper intent detail.
- Approve or reject for paper.
- Submit approved intent to local paper adapter.

API copy and route names should use paper terminology. No endpoint should imply live trading or broker routing.

### Frontend Layer

The frontend should connect the Candidate Review Board to paper simulation through an explicit review page.

Expected user flow:

- User opens a candidate experiment.
- User creates a paper intent draft.
- UI shows RiskGuard decision and audit timeline.
- User explicitly approves or rejects paper simulation.
- Approved paper intent can be submitted to the local paper adapter.

The UI must not include broker buy/sell controls, broker account selection, or language that implies live execution.

### Agent and MCP Boundary

Agent-originated trading-class actions remain disabled until a paper scope is explicitly added and tested.

If an agent-facing paper write path is later added, it must require:

- Paper-only scope.
- Instrument allowlist.
- Idempotency key.
- Rate limit.
- RiskGuard pass.
- Audit event.
- Human approval unless a separate explicit auto-paper gate exists.

MCP tools must remain thin wrappers over Agent Gateway APIs and must not bypass backend checks.

## Data Flow

1. Candidate experiment is selected from Phase 4 Candidate Review Board.
2. Backend creates a draft paper intent linked to the candidate experiment id.
3. RiskGuard validates account status, symbol, asset class, quantity, price, estimated notional, daily limit, and option metadata.
4. Backend stores the decision and appends an audit event.
5. User reviews the intent, risk decision, and source experiment.
6. User approves or rejects paper simulation.
7. Approved intent is submitted to the local paper adapter.
8. Adapter creates a simulated fill and updates paper position and cash.
9. Backend appends audit events for submission, fill, and position update.

## Error Handling

Use explicit rejection states rather than silent fallback.

Expected denials:

- Missing or archived paper account.
- Instrument not allowlisted.
- Unsupported asset class.
- Non-positive quantity.
- Non-positive limit price.
- Missing option contract metadata for option intents.
- Estimated notional above limit.
- Candidate experiment missing or not in candidate state.
- Idempotency-key conflict.
- Attempted broker credential or broker route payload.

Every denial should return a stable reason code and append an audit event when it occurs after intent creation.

## Testing Strategy

Implementation should use test-first slices:

- Contract tests for schemas and allowed statuses.
- RiskGuard tests for each pass and rejection path.
- Persistence tests for state transitions and append-only audit records.
- API tests for idempotency, authorization, review, and paper-only terminology.
- Adapter tests proving the paper adapter has no broker or network dependency.
- Frontend build and copy checks for paper-only language.
- Repository grep checks for forbidden broker/live execution additions.

Ubuntu remains the default verification environment through `ssh yasin-ubuntu`.

## Safety Boundary

Phase 5 allows:

- Paper account simulation.
- Paper order intents.
- RiskGuard validation.
- Human review.
- Local paper fills.
- Paper positions.
- Append-only audit.

Phase 5 forbids:

- Live broker order placement.
- Broker credentials.
- Broker account mutation.
- Live order status sync.
- AI-direct live trading.
- MCP tools that place broker orders.
- Automatic candidate-to-paper promotion without review.
- Automatic paper-to-live promotion.

## Open Decisions

The following choices should be made during implementation planning, not during this design step:

- Exact database table names.
- Whether Slice 2 uses Pydantic schemas only or introduces SQLAlchemy models immediately.
- Initial default paper account limits.
- Whether paper fills use last price, midpoint, or deterministic fixture prices in the first adapter.

## Approval Gate

This spec is ready for implementation planning when:

- The user accepts the paper-only scope.
- The roadmap points Phase 5 to paper architecture first.
- Project status is updated to Phase 5 planning.
- Yasin Brain records that live execution remains out of scope.
