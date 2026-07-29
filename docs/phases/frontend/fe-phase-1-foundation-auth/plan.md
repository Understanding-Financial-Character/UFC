# FE Phase 1 - Foundation Auth

## Status
NOT_STARTED
## Goal
Build frontend app foundation and auth flow against BE Phase 3.
## Why
User workflows need bearer-token auth before protected group screens.
## Prerequisites
BE Phase 3.
## In Scope
App shell, routing, API client, signup/login/session state.
## Out of Scope
Transaction analysis flow and results.
## Responsible Modules
`frontend/src/app`, `frontend/src/features`, `frontend/src/api`, tests.
## Contracts
Auth and `/me` API contracts.
## Data Changes
None.
## Security Considerations
No token logging; browser storage policy must be documented.
## Implementation Tasks
Implement auth UI/API client.
## Test Scenarios
Signup, login, logout, refresh failure, protected routes.
## Completion Criteria
Frontend build/lint/tests pass.
## Branch
`feat/fe-phase-1-foundation-auth`
## Dependencies
BE Phase 3.
