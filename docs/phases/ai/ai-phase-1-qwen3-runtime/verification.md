# AI Phase 1 - Qwen3 Runtime Verification

## Verified Commit
Verified commits:

- `fac064b` feat: add qwen3 ollama report runtime
- `5bd791e` fix: harden ollama runtime error handling
## Verified At
2026-07-30 10:17:04 KST
## Environment
macOS local development environment with Docker Compose.
## Commands
- `docker compose -f compose.yaml -f compose.dev.yaml config`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend alembic upgrade head`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend pytest tests/test_ai_qwen_runtime.py`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend pytest`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend ruff check app tests`
- `make verify`
- `docker compose -f compose.yaml -f compose.dev.yaml --profile ai config`
- `make -n ai-smoke`
- `git diff --check`
## Results
- Compose config passed.
- Alembic upgrade passed with no new migration.
- AI runtime unit tests passed after review hardening: 18 tests.
- Full backend test suite passed after review hardening: 57 tests.
- Backend Ruff passed.
- `make verify` passed, including backend tests, backend lint, frontend lint, frontend build, migration, and whitespace checks.
- AI profile Compose config passed.
- `make -n ai-smoke` confirmed the Ollama smoke command path without pulling or running `qwen3:4b`.
- Review hardening covered direct `/api/generate` generation, HTTP 400/404/500 classification, optional template fallback, and thinking-mode prompt behavior.
## API Evidence
Not applicable. No new API route was added.
## DB Evidence
No migration or model change.
## Security Evidence
- AI report request DTO excludes user email, user name, nickname, internal user id, full transaction arrays, raw transaction memo text, tokens, ciphertext, and secrets.
- Qwen prompt is built from aggregate evidence only.
- `LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_THINKING_ENABLED`, `LLM_TEMPERATURE`, and `LLM_TIMEOUT_SECONDS` are environment-driven.
## Known Limitations
- Prompt wording is intentionally minimal and not final.
- Analysis orchestration and `ai_reports` persistence are not connected in this phase.
- Real `qwen3:4b` generation was not executed locally; provider behavior is covered by unit tests and `make -n ai-smoke`.
