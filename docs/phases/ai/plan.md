# AI Phase Plan

## Phase Goal

### AI Phase 1

Define the deterministic analysis input/output contract and calculate spending behavior metrics before any LLM report generation.

### Later AI Report Phase

Implement AI report generation from deterministic analysis outputs without making unsupported claims.

## Implementation Scope

### AI Phase 1

- Concrete `analysis-input-v1` schema
- Concrete `behavior-metrics-v1` schema
- Deterministic behavior metric calculation
- Metric evidence generation
- Minimum data and missing-value policy

### Later AI Report Phase

- Prompt input contract
- LLM client boundary
- Report response parsing
- Uncertainty-aware report wording
- AI failure handling

## Excluded Scope

- UI-specific final report data guessing
- Analysis result persistence schema
- Transaction upload API
- Spending MBTI final type calculation
- LLM-based score calculation
- LLM calls in AI Phase 1
- Personality diagnosis
- Financial product recommendation

## Modules Expected To Change

- `backend/app/ai`
- `backend/app/analysis`
- `backend/tests`
- `docs/contracts`

## Prerequisites

- AI Phase 1 only requires concrete analysis input and behavior metrics contracts.
- Later AI report work requires analysis output to be concrete enough for prompt inputs.
- Later AI report work requires backend analysis result persistence or test stubs.

## Completion Criteria

### AI Phase 1

- Normal, concentrated, repeated, and volatile spending scenarios are covered by tests.
- Running the same input produces the same output.
- Metric evidence is generated.
- Input and output schema versions exist.
- Missing-value and minimum-data policies are documented.

### Later AI Report Phase

- AI reports cite only provided evidence.
- Provisional results remain clearly marked.
- AI error responses follow the error contract.
- Tests cover success, sparse data, and LLM failure paths.
