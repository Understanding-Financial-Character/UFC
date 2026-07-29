# AN Phase 1 - Preprocessing and Data Quality

## Status
NOT_STARTED
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
Implement preprocessing and quality DTOs.
## Test Scenarios
Missing categories, missing merchant, sparse data, synthetic data, tri-state signals.
## Completion Criteria
Quality outputs and tests verified.
## Branch
`feat/an-phase-1-preprocessing-quality`
## Dependencies
BE Phase 4.
