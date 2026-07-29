# BE Phase 5 - Analysis Persistence

## Status
NOT_STARTED
## Goal
Persist analysis runs, behavior metrics, rule results, and AI report records.
## Why
Backend needs durable analysis state independent from group readiness.
## Prerequisites
BE Phase 4 and analysis contracts.
## In Scope
`analysis_runs`, `behavior_metrics`, `consumption_mbti_results`, `ai_reports` persistence.
## Out of Scope
Metric calculation, rule evaluation, Qwen generation.
## Responsible Modules
`backend/app/modules`, `backend/app/db`, migrations, tests.
## Contracts
Analysis persistence contracts.
## Data Changes
Future migrations for analysis result tables.
## Security Considerations
Report text and sensitive source references must be minimized and masked.
## Implementation Tasks
Define models, migrations, repository/service layer, tests.
## Test Scenarios
Status/result status separation, nullable MBTI, AI report status.
## Completion Criteria
Persistence and verification complete.
## Branch
`feat/be-phase-5-analysis-persistence`
## Dependencies
BE Phase 4, AN Phase 2/3 contracts.
