# BE Phase 4 - Transaction Input

## Status
NOT_STARTED
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
Future migrations for `categories` and `transactions`.
## Security Considerations
Sensitive financial data handling and encrypted free-text policy.
## Implementation Tasks
Define schemas, models, migrations, APIs, tests.
## Test Scenarios
Upload/mock/manual validation, owner access, tri-state booleans.
## Completion Criteria
APIs, migrations, tests, docs, and verification complete.
## Branch
`feat/be-phase-4-transaction-input`
## Dependencies
BE Phase 3.
