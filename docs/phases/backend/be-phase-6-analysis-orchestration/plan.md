# BE Phase 6 - Analysis Orchestration

## Status
NOT_STARTED
## Goal
Coordinate transaction lookup, analysis execution, rule results, persistence, and AI report triggering.
## Why
Analysis workflow needs explicit state transitions and failure boundaries.
## Prerequisites
BE Phase 5, AN Phase 3, AI runtime/report phases.
## In Scope
Analysis run API, orchestration state transitions, retry/failure handling.
## Out of Scope
New metric formulas, rule definitions, frontend UI.
## Responsible Modules
`backend/app/orchestration`, `backend/app/modules`, tests.
## Contracts
Analysis run API contracts.
## Data Changes
No new tables beyond BE Phase 5 unless explicitly approved.
## Security Considerations
Owner checks on analysis and report resources.
## Implementation Tasks
Define orchestration services and tests.
## Test Scenarios
Success, insufficient data, AI failure, owner denial.
## Completion Criteria
End-to-end backend analysis path verified.
## Branch
`feat/be-phase-6-analysis-orchestration`
## Dependencies
BE Phase 5, AN Phase 3, AI Phase 2.
