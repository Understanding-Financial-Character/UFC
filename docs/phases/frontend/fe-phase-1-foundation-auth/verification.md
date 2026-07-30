# FE Phase 1 - Foundation Auth Verification

## Verified Commit
Pending final commit.

## Verified At
2026-07-30 Asia/Seoul

## Environment
Windows PowerShell, Node.js v24.18.0, npm, Vite frontend workspace, Docker Compose with Docker Desktop engine access granted for container checks.

## Commands
- `npm.cmd install`
- `npm.cmd rebuild esbuild`
- `npm.cmd run lint`
- `npm.cmd run test`
- `npm.cmd run build`
- `docker compose -f compose.yaml -f compose.dev.yaml config`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend alembic upgrade head`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend pytest`
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend ruff check app tests`
- `git diff --check`

## Results
- `npm.cmd install`: passed; generated `frontend/package-lock.json`. npm reported 12 audit vulnerabilities in the dependency tree.
- `npm.cmd rebuild esbuild`: passed with elevated permissions after sandbox `spawn EPERM`.
- `npm.cmd run lint`: passed.
- `npm.cmd run test`: passed; 1 test file, 2 tests.
- `npm.cmd run build`: passed; TypeScript and Vite production build completed.
- `docker compose -f compose.yaml -f compose.dev.yaml config`: passed with verification-only environment variables supplied because local `.env` was not initialized.
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend alembic upgrade head`: passed; migrations applied through `20260729_0003`.
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend pytest`: passed on rerun with compliant verification-only secrets; 39 passed, 1 existing TestClient deprecation warning.
- `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend ruff check app tests`: failed with `EXE002` on 38 existing Python files because the Windows bind mount presented normal `100644` Git files as executable inside the container.
- `git diff --check`: passed.

## API Evidence
Auth endpoints are wired to documented BE Phase 3 paths: `/api/v1/auth/signup`, `/api/v1/auth/login`, `/api/v1/auth/refresh`, `/api/v1/auth/logout`, and `/api/v1/me`.

## DB Evidence
No schema changes were made. Alembic upgrade to head passed in Docker Compose.

## Security Evidence
- Passwords are local form values and are not stored in Redux.
- Refresh token plaintext is excluded from Redux state and browser persistent storage; it is handled only through in-memory `refreshTokenStorage`.
- Access token is stored in Redux in-memory state for Authorization header preparation.
- 401 refresh retry clears local session state and refresh token storage when refresh fails.

## Known Limitations
- Refresh token persistence is intentionally in-memory only; page reloads require login again until the backend supports an HttpOnly-cookie refresh strategy.
- No real browser E2E test was added in this phase.
- npm audit reported dependency vulnerabilities; no automatic audit fix was applied because it may alter versions beyond phase scope.
- Backend ruff in Docker Compose dev mode is blocked on this Windows bind mount by `EXE002`; tracked Git modes checked for sampled files are `100644`.
