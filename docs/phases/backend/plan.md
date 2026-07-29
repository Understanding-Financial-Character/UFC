# Backend Phase Plan

## Phase Goal

Implement backend APIs and persistence for MVP workflows after contracts are finalized.

## Implementation Scope

### BE Phase 1 - FastAPI Foundation

- FastAPI application entrypoint
- Settings management
- PostgreSQL connectivity
- SQLAlchemy 2.x session foundation
- Alembic upgrade path
- Shared response and error shape
- Request `trace_id`
- Health and readiness checks
- Backend test environment
- Docker Compose backend and database connectivity
- OpenAPI base configuration

### Later Backend Slices

- Groups and members
- Member MBTI registration
- Transaction ingestion or mock scenario selection
- Analysis orchestration endpoints
- Spending MBTI result retrieval

### BE Phase 2 - User, Group, and Member Domain

- Basic local user signup before full login
- Temporary user identity through `X-UFC-User-Id`
- Group create, list, get, and patch APIs
- Group owner verification
- Group member add, patch, and delete APIs
- Member MBTI validation against the 16 valid MBTI types
- 2-4 member readiness rule
- Group readiness status and `can_analyze` calculation without depending on analysis result schemas

## Excluded Scope

- Real bank account connection
- Transfers and automatic payments
- Credit score analysis
- Financial product recommendation
- Full login, password, session, OAuth, or JWT implementation for BE Phase 2
- Transaction upload and analysis execution for BE Phase 2
- Analysis run status on `Group`; later phases must model analysis execution separately

## Modules Expected To Change

- `backend/app/modules`
- `backend/app/api`
- `backend/app/core`
- `backend/app/db`
- `backend/migrations`
- `backend/tests`
- `docs/contracts`

## Prerequisites

- Phase 0 tracking standards are complete.
- Phase 0 tracking standards are complete.
- Foundation endpoints are documented before BE Phase 1 implementation.
- First vertical slice API contracts are finalized before domain API implementation starts.
- MVP authentication approach is decided and recorded in an ADR before domain APIs are implemented.
- User, Group, and Membership authorization model is finalized at contract level before domain APIs are implemented.
- Public share link access and expiration policy is decided before share card APIs are implemented.

## Completion Criteria

- Backend APIs match documented contracts.
- Database migrations are reproducible.
- Backend tests pass.
- Phase progress and verification are updated.
