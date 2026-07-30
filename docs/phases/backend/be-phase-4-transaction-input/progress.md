# BE Phase 4 - Transaction Input Progress

## Current Status
IMPLEMENTED
## Implemented
- `categories` and `transactions` SQLAlchemy models.
- `group_members.status` with `ACTIVE` membership validation for transaction member assignment.
- Alembic migration `20260730_0004_transaction_input`.
- Category seed fixture owned by immutable migration data.
- CSV import API with row-level validation.
- CSV contract narrowed to persisted fields only; unused fields such as currency and client-supplied source metadata are rejected.
- Length overflow, invalid UUIDs, non-finite amounts, and timezone-less datetimes are rejected instead of silently normalized.
- Amounts exceeding the `Numeric(14, 2)` storage range are rejected as row-level `AMOUNT_OUT_OF_RANGE` errors.
- Rejected rows no longer reserve their `source_row_key` inside the current import batch.
- Mock scenario list/apply APIs using synthetic `transactions_mock_v2.csv`.
- Mock scenario application now rejects member count mismatches instead of modulo-mapping source members.
- Transaction list, update, and delete APIs.
- Ownership checks through bearer-authenticated group owner validation.
- Integration tests for required Phase 4 scenarios.
## Remaining
No Phase 4 implementation tasks remaining.
## Contract Changes
Updated `docs/contracts/api-contracts.md` for categories, mock scenarios, transaction import/list/update/delete.
## Migration Changes
Added `20260730_0004_transaction_input`, including category seed rows and transaction constraints.
## Linked PR
Not assigned.
## Commits
Pending final commit.
## Blockers
None.
## Handover Notes
Do not treat `NULL` transaction signals as `FALSE`. User-provided MBTI scenario notes belong to later Feature Catalog and Rule Catalog phases, not BE Phase 4.
