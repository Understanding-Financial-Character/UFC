# BE Phase 5 - Analysis Persistence Verification

## Verified Commit
`96758c0` feat: add analysis persistence schema

`c4d6ee4` fix: align analysis persistence contracts
## Verified At
2026-07-30 13:20:58 KST
## Environment
macOS local development environment with Docker Compose.
## Commands
- `docker compose -f compose.yaml -f compose.dev.yaml config`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend pytest tests/test_analysis_persistence.py`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend ruff check app tests`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend alembic upgrade head`
- `make reset CONFIRM=1`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend alembic downgrade 20260730_0004`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend alembic upgrade head`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend pytest`
- `make migration-check`
- `make verify`
- `git diff --check`
## Results
- Compose config passed.
- Analysis persistence tests passed: 11 tests.
- Full backend test suite passed: 113 tests.
- Backend Ruff passed.
- Alembic upgrade to `20260730_0005` passed on PostgreSQL.
- Local PostgreSQL volume was reset because an earlier unmerged version of revision `20260730_0005` had already been applied before review hardening.
- Alembic downgrade from `20260730_0005` to `20260730_0004` passed.
- Alembic re-upgrade from `20260730_0004` to `20260730_0005` passed.
- `make migration-check` reported `20260730_0005 (head)`.
- Final `make verify` passed, including backend tests, backend lint, frontend lint, frontend build, migration, and whitespace checks.
## API Evidence
Not applicable. No API route was added in this phase.
## DB Evidence
- `analysis_runs` stores execution `status` separately from result `result_status`.
- `analysis_runs.result_status` is nullable for `PENDING` and `RUNNING` and required for `COMPLETED`.
- `analysis_runs.result_status` is forced null for `FAILED`.
- `behavior_metrics` stores AN Phase 2 core feature fields and `metric_metadata.axisContributions`.
- `UNAVAILABLE` behavior metrics cannot store `raw_value` or `normalized_score`; `AVAILABLE` metrics cannot store `unavailable_reason`.
- `behavior_metrics.metric_metadata` is PostgreSQL JSONB in the migrated database.
- `consumption_mbti_results.mbti_type` is nullable and DB/repository validation prevents forced MBTI for `INSUFFICIENT_DATA`.
- `ai_reports` records `COMPLETED`, `FALLBACK_COMPLETED`, and `FAILED` status payloads with fallback consistency checks.
- Result tables store schema/version fields and inherit `snapshot_hash` from `analysis_runs` through repository writes.
## Security Evidence
- No raw transaction arrays, user email, token, secret, or ciphertext fields were added to analysis result tables.
- AI report persistence stores generated content and validation metadata, not Qwen input secrets or raw financial source rows.
## Known Limitations
- Analysis calculation, rule execution, Qwen calls, and analysis API orchestration remain out of scope.
- Direct ORM writes can still bypass repository snapshot inheritance and provisional-reason enum validation. DB constraints cover core lifecycle and payload invariants; BE Phase 6 should use `AnalysisResultRepository` for writes.
