# BE Phase 6 - Analysis Orchestration

## Status
IMPLEMENTED
## Goal
Coordinate transaction lookup, analysis execution, rule results, persistence, and AI report triggering.
## Why
Analysis workflow needs explicit state transitions and failure boundaries.
## Prerequisites
BE Phase 5, AN Phase 3, AI runtime/report phases.
## In Scope
Analysis run API, orchestration state transitions, full retry/report retry, failure handling.
## Out of Scope
New metric formulas, rule definitions, frontend UI.
## Responsible Modules
`backend/app/orchestration`, `backend/app/modules`, tests.
## Contracts
Analysis run API contracts.
## Data Changes
Extends `analysis_runs` with minimized `analysis_input_snapshot` JSON and nullable `retried_from_analysis_id` for failed-run snapshot retries.
## Security Considerations
Owner checks on analysis and report resources.
## Implementation Tasks
Implemented orchestration services, analysis APIs, state transition persistence, insufficient-data AI skip, snapshot-backed full retry policy, locked report-only retry policy, and tests.
## Test Scenarios
Success, insufficient data without AI generation, KST period boundaries, full retry policy, report-only retry policy, concurrent report retry rejection, snapshot-based report retry member summary, legacy snapshot rejection, AI failure, owner denial.
## Completion Criteria
End-to-end backend analysis path verified with synchronous MVP execution.
## Branch
`feat/be-phase-6-analysis-orchestration`
## Dependencies
BE Phase 5, AN Phase 3, AI Phase 2.
