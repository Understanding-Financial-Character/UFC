# Backend Phase Verification

## Status

`VERIFYING`

## Executed Commands

Docker Compose commands that start or configure the backend were executed with test-only values for `AUTH_TOKEN_SECRET`, `FIELD_ENCRYPTION_KEY`, `FIELD_LOOKUP_HMAC_KEY`, and `FIELD_KEY_VERSION`.

```bash
git status --short --branch
git fetch origin
git rev-list --left-right --count main...origin/main
docker compose -f compose.yaml -f compose.dev.yaml config
env -u AUTH_TOKEN_SECRET -u FIELD_ENCRYPTION_KEY -u FIELD_LOOKUP_HMAC_KEY -u FIELD_KEY_VERSION docker compose -f compose.yaml -f compose.dev.yaml config
docker compose -f compose.yaml -f compose.dev.yaml build backend
docker compose -f compose.yaml -f compose.dev.yaml run --rm backend pytest
docker compose -f compose.yaml -f compose.dev.yaml run --rm backend ruff check app tests
docker compose -f compose.yaml -f compose.dev.yaml run --rm backend alembic upgrade head
docker compose -f compose.yaml -f compose.dev.yaml up -d db backend
curl -s -i http://localhost:8000/health
curl -s -i http://localhost:8000/ready
curl -s -i http://localhost:8000/api/v1/meta
curl -s -o /private/tmp/ufc-openapi.json -w "%{http_code}" http://localhost:8000/api/v1/openapi.json
curl -s -o /private/tmp/ufc-api-v1-health.txt -w "%{http_code}" http://localhost:8000/api/v1/health
curl -s -o /private/tmp/ufc-api-v1-ready.txt -w "%{http_code}" http://localhost:8000/api/v1/ready
python3 -c "import json; data=json.load(open('/private/tmp/ufc-openapi.json')); print('/api/v1/health' in data['paths'], '/api/v1/ready' in data['paths'], '/health' in data['paths'], '/ready' in data['paths'], '/api/v1/meta' in data['paths'])"
```

## Test Results

- `pytest`: Passed, `39 passed, 1 warning`.
- Foundation tests cover health, readiness, meta, OpenAPI paths, sanitized validation errors, trace id handling, DB failure cleanup, and unhandled exception responses.
- BE Phase 2/3 tests cover authenticated signup, group creation and lookup, member add/update/delete, MBTI validation, 4-member limit, owner access blocking, readiness status transitions, name normalization, empty PATCH rejection, duplicate member name conflict, PostgreSQL API flow, and PostgreSQL concurrent member-add protection.
- BE Phase 3 security tests cover SEC-01 through SEC-07, login rate limiting, login counter clearing, refresh, logout, refresh token reuse family revocation, PostgreSQL concurrent refresh rotation, email AAD binding, and CORS origin restriction.
- `ruff check app tests`: Passed.
- `alembic upgrade head`: Passed against PostgreSQL, including `20260729_0002 -> 20260729_0003`.
- `docker compose config`: Passed when required security environment variables were provided.
- `docker compose config` without required security environment variables: Failed as expected.

## API Verification Results

- `GET /health`: `200 OK`, `{"status":"ok"}`, includes `X-Trace-Id`.
- `GET /ready`: `200 OK`, `{"status":"ready"}`, includes `X-Trace-Id`.
- `GET /api/v1/meta`: `200 OK`, returns app name, version, and environment.
- `GET /api/v1/openapi.json`: `200`.
- `GET /api/v1/health`: `404`.
- `GET /api/v1/ready`: `404`.
- OpenAPI path check: `/api/v1/health` and `/api/v1/ready` are absent; `/health`, `/ready`, and `/api/v1/meta` are present.

## Evidence

- Docker backend image built successfully.
- Compose validation was run with test-only security values; those values are not committed to repository configuration.
- PostgreSQL container was available during Alembic, pytest, and readiness checks.
- A Docker container name conflict occurred during parallel lint/test runs and was resolved with `docker compose -f compose.yaml -f compose.dev.yaml down`; no code or configuration change was required.
- TestClient warning details are documented in `docs/troubleshooting/backend-testclient-httpx-warning.md`.
- A Phase 2 migration enum duplication issue was found during PostgreSQL `alembic upgrade head` and fixed by letting table creation own enum creation.
- A Phase 3 development DB partial schema issue occurred after running metadata `create_all()` before Alembic and is documented in `docs/troubleshooting/backend-metadata-create-all-before-migration.md`.
- A refresh token concurrent rotation race was reviewed and documented in `docs/troubleshooting/refresh-token-concurrent-rotation.md`.

## Known Limitations

- Transaction APIs and analysis execution are not implemented in BE Phase 2.
- BE Phase 3 does not introduce transaction storage, financial free-text storage, or AI report persistence, so those future fields are not yet encrypted in a domain model.
- BE Phase 3 uses an environment-backed key provider; KMS integration is deferred.
- Login rate limiting is in-memory and must move to shared, IP-aware storage before multi-process production deployment.
- Access tokens use a minimal signed internal format in this MVP and should move to a maintained JOSE/JWT implementation in a later hardening phase.
- Email encryption now requires `user:{user_id}:email` AES-GCM AAD. Development data created by the earlier Phase 3 security commit without AAD must be reset or re-encrypted before `/api/v1/admin/users` can decrypt it.
- `refresh_tokens.replaced_by_token_id` stores the replacement id without a self-referential foreign key. Future audit hardening can add that constraint after delete policy is decided.
- Group readiness status is persisted even though it is currently derivable from members and MBTI completeness. Later phases should either keep it as a persisted read model with disciplined updates or remove persistence and derive it at response/query time.
- Member create/update maps `IntegrityError` to duplicate display-name conflict because `uq_group_member_name` is currently the relevant member-write constraint. Future hardening should inspect the PostgreSQL constraint name before translating database errors.
- The FastAPI TestClient/httpx deprecation warning remains non-blocking.
- Docker production/development target split is deferred to a later hardening slice.
