# AN Phase 2 - Behavior Metrics Verification

## Verified Commit
Pending final commit.
## Verified At
2026-07-30
## Environment
Docker Compose dev backend on PostgreSQL 16.
## Commands
- `docker compose -f compose.yaml -f compose.dev.yaml config`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend alembic upgrade head`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend pytest tests/test_behavior_metrics.py`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend pytest`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend ruff check app tests`
- `git diff --check`
## Results
- Compose config: passed.
- Alembic upgrade head: passed.
- AN Phase 2 behavior metric tests: 8 passed.
- Full backend tests: 83 passed, 1 upstream deprecation warning from FastAPI/Starlette TestClient.
- Ruff: passed.
- Diff whitespace check: passed.
## API Evidence
Not applicable.
## DB Evidence
No schema change in AN Phase 2. Existing migration chain applies cleanly to head.
## Security Evidence
- Feature engine consumes `NormalizedTransaction` dataclasses only.
- Analysis code does not import SQLAlchemy, FastAPI routers, or database sessions.
- Feature output contains aggregate values and evidence text, not raw account numbers, card numbers, credentials, tokens, ciphertext, or full transaction arrays for Qwen3.
## Known Limitations
- Axis weights, rule engine, final MBTI, DB persistence, API routing, and Qwen3 calls are out of scope.
- `NEW_MERCHANT_RATIO` treats the first occurrence in the provided normalized window as new because no historical merchant baseline exists in AN Phase 2.
