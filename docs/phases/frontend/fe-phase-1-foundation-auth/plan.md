# FE Phase 1 - Foundation Auth

## Status
COMPLETED

## Goal
Build frontend app foundation and auth flow against BE Phase 3.

## Why
User workflows need bearer-token auth before protected group screens.

## Prerequisites
BE Phase 3.

## In Scope
App shell, routing, Redux Toolkit store, RTK Query API client, signup/login/logout/session state, protected routing, role guard, common feedback UI.

## Out of Scope
Transaction analysis flow, group/member management screens, analysis results, admin data tables, and any frontend score calculation.

## Responsible Modules
`frontend/src/app`, `frontend/src/features`, `frontend/src/api`, `frontend/src/components`, `frontend/src/pages`, `frontend/tests`.

## Contracts
Consumes the BE Phase 3 auth and `/me` API contracts in `docs/contracts/api-contracts.md` without changing them.

## Data Changes
None.

## Security Considerations
Access tokens are held only in Redux in-memory session state. Refresh token plaintext is never stored in Redux or browser persistent storage and is isolated behind in-memory `refreshTokenStorage` for same-page refresh rotation. Passwords remain local form values only and are submitted directly to the auth API.

## Implementation Tasks
- Configure Redux Toolkit store and typed hooks.
- Add RTK Query `baseApi` with bearer header preparation.
- Add signup, login, logout, and `/me` endpoints.
- Add single-flight 401 refresh retry and session clearing on refresh failure.
- Add `ProtectedRoute` and `RoleGuard`.
- Add common Loading, Error, Empty, and Toast components.
- Add login, signup, 403, app shell, and not-found screens.
- Add reducer tests for token/session storage boundaries.

## Test Scenarios
Signup/login token handling, logout/session clearing, refresh failure path by implementation review, protected routes, role guard, frontend lint/test/build.

## Completion Criteria
Frontend lint, tests, and build pass.

## Branch
`feat/fe-phase-1-foundation-auth`

## Dependencies
BE Phase 3.
