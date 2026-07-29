# Backend Phase Progress

## Status

VERIFYING

## Implemented Work

- Added FastAPI application factory and configured OpenAPI metadata.
- Added `/health`, `/ready`, `/api/v1/health`, `/api/v1/ready`, and `/api/v1/meta`.
- Added settings fields for app version, API prefix, and log level.
- Added SQLAlchemy session foundation and database readiness query.
- Added Alembic upgrade verification against PostgreSQL.
- Added API router and dependency module.
- Added orchestration package boundary.
- Added request trace id middleware with `X-Trace-Id` response header.
- Added inbound trace id validation and trace id logging context.
- Added common API exception handling and normalized error body with `code`, `message`, `details`, and `traceId`.
- Sanitized validation error responses so raw input and validator context are not echoed.
- Removed duplicate `/api/v1/health` and `/api/v1/ready` endpoints from the API router.
- Added backend foundation tests, including a PostgreSQL readiness integration test when `DATABASE_URL` is available.
- Updated Dockerfile so editable backend installation succeeds in the image.
- Documented the reproducible FastAPI TestClient/httpx warning.
- Added BE Phase 2 `User`, `Group`, `GroupMember`, and `MemberPersonality` SQLAlchemy models.
- Added local user signup API for pre-login MVP identity.
- Added group create, list, get, and patch APIs.
- Added group member create, patch, and delete APIs.
- Added MBTI enum validation for all 16 MBTI values.
- Added owner-only group access checks using the temporary `X-UFC-User-Id` header.
- Added group member count and readiness status calculation, separated from future analysis execution status.
- Added whitespace normalization for user, group, and member names.
- Added empty PATCH request validation.
- Added group row locking for member additions and 409 handling for member display name constraint conflicts.
- Added Alembic migration for the Phase 2 domain tables and enums.
- Added integration tests for user, group, member, MBTI validation, member count limit, owner access, and status transitions.
- Added BE Phase 3 auth APIs for signup, login, refresh, logout, and `/me`.
- Replaced `X-UFC-User-Id` group authorization with bearer access-token principal checks.
- Added Argon2id password hashing and refresh token hash storage.
- Added `USER` and `ADMIN` roles with `/api/v1/admin/users` masked user summaries.
- Added AES-256-GCM field encryption helpers, email lookup HMAC, key version storage, and `KeyProvider` interface.
- Added required security setting validation and CORS origin configuration.
- Added login rate limiting and failed login lockout.
- Added Phase 3 security migration for user auth fields and refresh tokens.
- Added security tests SEC-01 through SEC-07 plus auth flow and rate-limit coverage.

## Changed Contracts

- Added backend foundation endpoint contracts for `/health`, `/ready`, `/api/v1/meta`, and `/api/v1/openapi.json`.
- Updated error contract from `request_id` to `traceId` to match BE Phase 1 requirement.
- Added `DATABASE_UNAVAILABLE` error code.
- Added Phase 2 user and group contracts, including `POST /api/v1/users` and temporary `X-UFC-User-Id` header principal checks.
- Updated group contract so group creation starts with zero members and member readiness is calculated after member registration.
- Updated group status contract to exclude analysis execution states from `Group.status`.
- Added Phase 3 auth/admin contracts and bearer-token protection for group APIs.
- Added auth/security error codes: `AUTHENTICATION_REQUIRED`, `PERMISSION_DENIED`, and `RATE_LIMITED`.

## Remaining Work

- Create PR for `feat/be-phase-3-security-baseline`.
- Record PR link and final merge commit after review.
- Transaction APIs remain for a later backend slice.
- Applying encryption to transaction, finance free-text, and AI report fields remains for the slice that introduces those persisted fields.
- Split production Docker image from development/test dependencies in a later hardening slice.

## Linked Branch, PR, Commits

- Branch: `feat/be-phase-3-security-baseline`
- PR: Pending
- Commits: Pending
