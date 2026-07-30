# BE Phase 4 - Transaction Input Verification

## Verified Commit
`3b8f211`
## Verified At
2026-07-30
## Environment
Docker Compose backend container on Windows host.
## Commands
- `python scripts\bootstrap_env.py`
- `docker compose -f compose.yaml -f compose.dev.yaml config`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend alembic upgrade head`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend pytest tests/test_transaction_input.py`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend pytest`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend ruff check app tests`
- `docker compose -p ufc_phase4_verify -f compose.yaml -f compose.dev.yaml run --rm backend alembic upgrade head`
- `git diff --check`
## Results
- Bootstrap created local `.env` and generated local secrets.
- Compose config passed. Output expands local secret values; do not paste raw output into shared docs.
- Alembic upgraded through `20260730_0004`.
- Phase 4 test file: 11 passed.
- Full backend pytest: 50 passed, 1 known TestClient/httpx deprecation warning.
- Ruff: passed after ignoring Windows bind-mount `EXE002`.
- Clean PostgreSQL migration was verified in a separate Compose project without deleting the existing local `ufc` database volume.
- `git diff --check`: passed with line-ending warnings only.
## API Evidence
- `GET /api/v1/categories` returns 42 active seed categories and performs no seed writes.
- `GET /api/v1/mock-scenarios` returns `mock-v2` with 358 synthetic transactions.
- `POST /api/v1/groups/{groupId}/transactions/import` persists accepted CSV rows and returns row-level validation errors for rejected rows.
- `POST /api/v1/groups/{groupId}/mock-scenarios/mock-v2/apply` applies synthetic mock transactions to the target group.
- `GET`, `PATCH`, and `DELETE /api/v1/groups/{groupId}/transactions/{transactionId}` paths covered by tests.
## DB Evidence
- Migration adds `categories`, `transactions`, `group_member_status`, `category_behavior_group`, `transaction_type`, and `transaction_source_type`.
- Category seed rows are loaded from immutable revision data at `backend/migrations/data/20260730_0004_categories.csv`; `GET /categories` is read-only.
- `transactions.amount > 0` check constraint.
- `transactions.source_row_key` unique per group.
- Nullable behavior signal columns have no server default.
## Security Evidence
- Transaction schema has no account number, card number, bank credential, access token, or refresh token columns.
- CSV import rejects sensitive header hints.
- Full CSV raw text is not logged.
- Group ownership enforced before import/list/update/delete.
## Known Limitations
- BE Phase 4 stores `behavior_group` but does not calculate behavior features, MBTI scores, analysis persistence, Qwen3 reports, or analysis execution.
- Mock scenario projection maps fixture member ids to target group active members deterministically when UUIDs differ.
- Docker compose config output includes expanded local secret values; verification notes intentionally summarize the result instead of preserving full output.
- The clean migration verification used a separate Compose project and left its named PostgreSQL volume in place to avoid destructive cleanup.
