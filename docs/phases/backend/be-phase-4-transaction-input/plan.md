# BE Phase 4 - Transaction Input

## Status
IMPLEMENTED
## Goal
Implement category and transaction input APIs for normalized source data.
## Why
Analysis requires persisted normalized transactions before orchestration.
## Prerequisites
BE Phase 3.
## In Scope
`categories`, `transactions`, mock/CSV/manual input contracts, tri-state transaction signals.
## Out of Scope
Analysis execution, MBTI rule engine, Qwen reports.
## Responsible Modules
`backend/app/modules`, `backend/migrations`, `backend/tests`, `docs/contracts`.
## Contracts
Transaction input API and category contracts.
## Data Changes
Migration `20260730_0004_transaction_input` adds `categories`, `transactions`, transaction/category enums, and `group_members.status`.
## Security Considerations
No account number, card number, bank credential, access token, or refresh token fields are accepted. CSV headers containing sensitive field hints are rejected. Full CSV raw text is not logged.
## Implementation Tasks
Implemented:

- SQLAlchemy models and DTO-separated Pydantic schemas.
- Alembic migration with category seed loading.
- CSV import with row-level validation results.
- Mock scenario apply API backed by synthetic CSV fixture.
- Transaction list, patch, and delete APIs.
- Bearer authentication and group ownership checks.
- Service-layer ACTIVE member and group relationship validation.
- `source_row_key` duplicate protection within a group.
## Test Scenarios
Covered by `backend/tests/test_transaction_input.py`:

- Normal CSV import.
- Invalid date, amount, and enum row errors.
- Missing category.
- Member from another group.
- Other user group access.
- Duplicate `source_row_key`.
- Nullable behavior signal preservation.
- Mock scenario application.
- `is_excluded` update and delete handling.
## Completion Criteria
APIs, migrations, tests, docs, and verification complete. Analysis feature calculation, MBTI scoring, analysis persistence, Qwen3 calls, and analysis execution APIs remain out of scope.
## Branch
`feat/be-phase-4-transaction-input`
## Dependencies
BE Phase 3.
