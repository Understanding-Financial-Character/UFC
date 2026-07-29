# FE Phase 5 - Admin Console

## Status
NOT_STARTED
## Goal
Implement safe admin operational screens.
## Why
Operators need masked status visibility.
## Prerequisites
BE Phase 7.
## In Scope
Admin login path integration, masked user summaries, analysis/report status views.
## Out of Scope
Raw transaction or raw report text access by default.
## Responsible Modules
`frontend/src/features`, `frontend/src/api`.
## Contracts
Admin API contracts.
## Data Changes
None.
## Security Considerations
ADMIN-only routes and masked data only.
## Implementation Tasks
Build admin console.
## Test Scenarios
USER denied, ADMIN allowed, masking, loading/error states.
## Completion Criteria
Frontend verification passes.
## Branch
`feat/fe-phase-5-admin-console`
## Dependencies
BE Phase 7.
