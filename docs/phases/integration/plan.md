# Integration Phase Plan

## Phase Goal

Verify the MVP works end to end across frontend, backend, PostgreSQL, deterministic analysis, and AI report boundaries.

## Implementation Scope

- End-to-end local workflow validation
- Docker Compose validation
- Contract compatibility checks
- Seed or mock scenario validation
- Result and report verification

## Excluded Scope

- Production deployment
- Real bank integration
- Payment execution
- Credit score analysis
- Financial product recommendation

## Modules Expected To Change

- `compose.yaml`
- `compose.dev.yaml`
- `mock-data`
- `docs/phases/integration`
- Tests or scripts required for integration verification

## Prerequisites

- Backend, AI, and frontend phases have completed their MVP slices.

## Completion Criteria

- Local end-to-end path is reproducible.
- Known limitations are documented.
- Verification evidence is recorded.
- No MVP-excluded feature is introduced.
