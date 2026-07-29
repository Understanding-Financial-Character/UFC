# Backend Phase Plan

## Phase Goal

Implement backend APIs and persistence for MVP workflows after contracts are finalized.

## Implementation Scope

- Groups and members
- Member MBTI registration
- Transaction ingestion or mock scenario selection
- Analysis orchestration endpoints
- Spending MBTI result retrieval

## Excluded Scope

- Real bank account connection
- Transfers and automatic payments
- Credit score analysis
- Financial product recommendation

## Modules Expected To Change

- `backend/app/modules`
- `backend/app/db`
- `backend/migrations`
- `backend/tests`
- `docs/contracts`

## Prerequisites

- Phase 0 tracking standards are complete.
- First vertical slice API contracts are finalized before implementation starts.
- MVP authentication approach is decided and recorded in an ADR.
- User, Group, and Membership authorization model is finalized at contract level.
- Public share link access and expiration policy is decided before share card APIs are implemented.

## Completion Criteria

- Backend APIs match documented contracts.
- Database migrations are reproducible.
- Backend tests pass.
- Phase progress and verification are updated.
