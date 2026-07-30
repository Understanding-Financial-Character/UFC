# BE Phase 6 - Analysis Orchestration Verification

## Verified Commit
`9fb4390`
## Verified At
2026-07-30
## Environment
Docker Compose dev backend on PostgreSQL 16. Alembic was verified against isolated database `ufc_phase6_review` because the reusable default local PostgreSQL volume had stale test-created tables.
## Commands
- `docker compose -f compose.yaml -f compose.dev.yaml config`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm -e DATABASE_URL=postgresql+psycopg://ufc:ufc@db:5432/ufc_phase6_review backend alembic upgrade head`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend pytest tests/test_analysis_orchestration.py tests/test_analysis_persistence.py`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend pytest`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend ruff check app tests`
- `git diff --check`
## Results
- Compose config: passed.
- Alembic upgrade head on isolated PostgreSQL database: passed.
- BE Phase 6 orchestration and persistence tests: 20 passed.
- Full backend tests: 145 passed, 1 upstream FastAPI/Starlette TestClient deprecation warning.
- Ruff: passed.
- Diff whitespace check: passed.
## API Evidence
- Create analysis executes synchronously and returns a pollable `AnalysisResponse`.
- Get analysis and latest group analysis return persisted deterministic results and AI report status.
- `INSUFFICIENT_DATA` skips AI report generation while preserving deterministic rows.
- Analysis period filtering uses `Asia/Seoul` calendar boundaries converted to UTC.
- Retry is rejected for completed runs and reserved for failed snapshot re-execution.
- AI report-only retry updates the failed report on the same analysis run without increasing behavior metrics or changing the consumption MBTI result.
- Legacy failed analyses with missing input snapshots return `409 ANALYSIS_SNAPSHOT_UNAVAILABLE`.
- Other users receive `404 NOT_FOUND` for inaccessible analyses.
- Active group run conflict returns `409 ANALYSIS_ALREADY_RUNNING`.
## DB Evidence
- Migration `20260730_0006` extends `analysis_run_status`.
- `analysis_runs.result_status` lifecycle check now supports `READY`, `ANALYZING`, `REPORT_GENERATING`, `PARTIALLY_COMPLETED`, and `COMPLETED_WITH_FALLBACK`.
- Behavior metrics, consumption MBTI result, AI report, schema versions, rule version, analysis version, minimized input snapshot, retry source link, and snapshot hash are persisted in one orchestration flow.
## Security Evidence
- All analysis APIs require bearer authentication.
- Group ownership is checked for create, get, latest, and retry.
- SQLAlchemy entities are converted to analysis DTOs before entering `app.analysis`.
- AI report generation receives aggregate evidence, axis scores, confidence, member MBTI counts, limitations, and result status only.
- Persisted analysis snapshots exclude raw CSV, account/card/bank fields, descriptions, and unnormalized merchant text.
## Known Limitations
- MVP implementation is synchronous rather than queue-backed.
- Default local PostgreSQL volume had stale branch/test schema state; see `docs/troubleshooting/stale-local-postgres-volume-after-branch-switch.md`.
