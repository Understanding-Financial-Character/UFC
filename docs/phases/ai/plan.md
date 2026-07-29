# AI Phase Plan

## Phase Goal

Implement AI report generation from deterministic analysis outputs without making unsupported claims.

## Implementation Scope

- Prompt input contract
- LLM client boundary
- Report response parsing
- Uncertainty-aware report wording
- AI failure handling

## Excluded Scope

- LLM-based score calculation
- Personality diagnosis
- Financial product recommendation

## Modules Expected To Change

- `backend/app/ai`
- `backend/app/analysis`
- `backend/tests`
- `docs/contracts`

## Prerequisites

- Analysis output contract is concrete enough for prompt inputs.
- Backend analysis result persistence exists or is stubbed for tests.

## Completion Criteria

- AI reports cite only provided evidence.
- Provisional results remain clearly marked.
- AI error responses follow the error contract.
- Tests cover success, sparse data, and LLM failure paths.
