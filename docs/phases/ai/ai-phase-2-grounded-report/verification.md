# AI Phase 2 - Grounded Report Verification

## Verified Commit
`6e618d6` feat: add grounded qwen report validation

`6db1d21` fix: harden grounded report validation

`32099bc` fix: add evidence value types for grounded reports
## Verified At
2026-07-30 11:31:37 KST
## Environment
macOS local development environment with Docker Compose.
## Commands
- `docker compose -f compose.yaml -f compose.dev.yaml config`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend alembic upgrade head`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend pytest tests/test_ai_grounded_report.py`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend pytest`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend ruff check app tests`
- `make reset CONFIRM=1`
- `docker compose -f compose.yaml -f compose.dev.yaml build frontend`
- `make verify`
- `git diff --check`
## Results
- Compose config passed.
- Alembic upgrade passed after local PostgreSQL volume reset.
- Grounded report unit tests passed: 17 tests.
- Full backend test suite passed: 85 tests.
- Backend Ruff passed.
- Initial `make verify` failed at frontend build due stale frontend Docker image after `main` dependency changes.
- Rebuilding the frontend image fixed the stale dependency issue.
- Final `make verify` passed, including backend tests, backend lint, frontend lint, frontend build, migration, and whitespace checks.
## API Evidence
Not applicable. No new API route was added.
## DB Evidence
No migration or model change was added in this phase.
## Security Evidence
- Grounded report input excludes email, nickname, internal user id, full transactions, transaction memo text, ciphertext, token, and secret keys.
- Report validation rejects unsupported numeric claims, changed spending MBTI, real diagnosis wording, financial product recommendation wording, and unknown output fields.
- Numeric validation uses only the same top-five evidence prompt context sent to Qwen3.
- Evidence value type prevents count, amount, duration, score, and text evidence from being validated as percentages.
- Prohibited input validation checks nested keys structurally and rejects email-like values.
- Template fallback uses structured metric/value text instead of raw basis or raw limitations and formats values by evidence type.
- Qwen3 receives only spending MBTI, axis scores, confidence, top evidence, member MBTI summary, limitations, and result status.
## Known Limitations
- Real `qwen3:4b` generation was not executed locally.
- Analysis orchestration and `ai_reports` persistence are not connected in this phase.
- Template fallback returns a deterministic structured report but does not mark database status; status mapping remains orchestration/persistence responsibility.
- Unsupported-claim validation remains a limited rule-based guardrail and does not prove full semantic entailment.
- Local troubleshooting was documented for stale PostgreSQL volumes and stale frontend Docker images.
