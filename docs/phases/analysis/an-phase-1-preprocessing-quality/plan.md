# AN Phase 1 - Preprocessing and Data Quality

## Status
IMPLEMENTED
## Goal
Convert normalized transactions into quality-checked analysis input.
## Why
Metrics and rules must not infer missing data or treat unknown values as false.
## Prerequisites
BE Phase 4 transaction input.
## In Scope
Analysis input adapter, data quality flags, sufficiency checks, tri-state handling.
## Out of Scope
Behavior metric formulas, final MBTI, Qwen reports.
## Responsible Modules
`backend/app/analysis`, `backend/tests`, `docs/analysis`.
## Contracts
Analysis input DTO and quality policy.
## Data Changes
None.
## Security Considerations
No raw personal identifiers in analysis DTO unless explicitly required.
## Implementation Tasks
Implemented DB-independent analysis dataclasses, transaction filtering policy, UTC and merchant-key normalization, data-quality scoring, provisional reasons, and limitations.
## Test Scenarios
Covered excluded transaction types, source-excluded rows, timezone normalization, merchant-key normalization, sparse data, synthetic data, missing category and merchant coverage, tri-state signals, and invalid contract inputs.
## Completion Criteria
Quality outputs and tests verified.
## Branch
`feat/an-phase-1-preprocessing-quality`
## Dependencies
BE Phase 4.
