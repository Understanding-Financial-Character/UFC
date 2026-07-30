# BE Phase 6 - Analysis Orchestration Verification

## Verified Commit
`d25b552`
## Verified At
2026-07-30
## Environment
Docker Compose dev backend on PostgreSQL 16. Alembic was verified against isolated database `ufc_phase6_verify` because the reusable default local PostgreSQL volume had stale test-created tables.
## Commands
- `docker compose -f compose.yaml -f compose.dev.yaml config`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm -e DATABASE_URL=postgresql+psycopg://ufc:ufc@db:5432/ufc_phase6_verify backend alembic upgrade head`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend pytest tests/test_analysis_orchestration.py`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend pytest tests/test_analysis_persistence.py tests/test_analysis_preprocessing.py tests/test_analysis_orchestration.py`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend pytest`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend ruff check app tests`
- `git diff --check`
## Results
- Compose config: passed.
- Alembic upgrade head on isolated PostgreSQL database: passed.
- BE Phase 6 orchestration tests: 4 passed.
- Affected backend tests: 22 passed.
- Full backend tests: 140 passed, 1 upstream FastAPI/Starlette TestClient deprecation warning.
- Ruff: passed.
- Diff whitespace check: passed.
## API Evidence
- Create analysis executes synchronously and returns a pollable `AnalysisResponse`.
- Get analysis and latest group analysis return persisted deterministic results and AI report status.
- Retry creates a new analysis run for the same group and period.
- Other users receive `404 NOT_FOUND` for inaccessible analyses.
- Active group run conflict returns `409 ANALYSIS_ALREADY_RUNNING`.
## DB Evidence
- Migration `20260730_0006` extends `analysis_run_status`.
- `analysis_runs.result_status` lifecycle check now supports `READY`, `ANALYZING`, `REPORT_GENERATING`, `PARTIALLY_COMPLETED`, and `COMPLETED_WITH_FALLBACK`.
- Behavior metrics, consumption MBTI result, AI report, schema versions, rule version, analysis version, and snapshot hash are persisted in one orchestration flow.
## Security Evidence
- All analysis APIs require bearer authentication.
- Group ownership is checked for create, get, latest, and retry.
- SQLAlchemy entities are converted to analysis DTOs before entering `app.analysis`.
- AI report generation receives aggregate evidence, axis scores, confidence, member MBTI counts, limitations, and result status only.
## Known Limitations
- MVP implementation is synchronous rather than queue-backed.
- Default local PostgreSQL volume had stale branch/test schema state; see `docs/troubleshooting/stale-local-postgres-volume-after-branch-switch.md`.
