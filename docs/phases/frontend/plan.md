# Frontend Phase Plan

## Phase Goal

Implement MVP user workflows and result exploration screens against documented backend contracts.

## Implementation Scope

- Group setup
- Member MBTI input
- Transaction upload or mock scenario selection
- Spending MBTI result view
- Comparison and graph views
- AI report and share card views

## Excluded Scope

- Direct LLM API calls
- Authoritative analysis calculations in the browser
- Real bank account connection UX
- Financial product recommendation UX

## Modules Expected To Change

- `frontend/src/app`
- `frontend/src/pages`
- `frontend/src/features`
- `frontend/src/components`
- `frontend/src/api`
- `frontend/src/types`
- `frontend/tests`

## Prerequisites

- API contracts are concrete enough for frontend integration.
- Backend endpoint behavior is available or mocked.

## Completion Criteria

- MVP screens follow documented contracts.
- Loading, error, empty, and provisional analysis states are represented.
- Frontend tests and build pass.
- Phase progress and verification are updated.
