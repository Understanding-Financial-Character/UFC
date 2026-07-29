# Refresh Token Concurrent Rotation Race

## Problem

Two requests using the same refresh token at nearly the same time could both observe the token as active if rotation was not protected by a database lock.

## Impact

Concurrent use of one refresh token can issue more than one replacement token. That weakens single-use refresh token semantics before financial transaction and analysis data are introduced.

## Reproduction

1. Create a user through `POST /api/v1/auth/signup`.
2. Send two concurrent `POST /api/v1/auth/refresh` requests with the same refresh token against PostgreSQL.
3. Without row-level locking, both requests can succeed depending on timing.

## Cause

Refresh token rotation needs to read, revoke, and replace the token as one serialized operation. A plain lookup does not prevent two database sessions from reading the same active row before either commits revocation.

## Alternatives Considered

- Add `SELECT ... FOR UPDATE` on the refresh token row and keep rotation in one transaction.
- Add a partial unique index for active token families.
- Accept the MVP limitation and document it.

## Resolution

BE Phase 3 uses `SELECT ... FOR UPDATE` when loading refresh tokens for rotation. The used token is revoked and the replacement token is inserted in the same transaction. Token records are linked with `family_id` and `replaced_by_token_id`.

If a revoked token is reused, the backend treats it as refresh token reuse, revokes active tokens in the same family with `REUSE_DETECTED`, and logs a warning without token values.

## Verification

- SQLite API tests verify refresh token reuse revokes the family.
- PostgreSQL integration coverage sends two concurrent refresh requests with the same token and expects one `200`, one `401`, one replacement token row, and family revocation after reuse detection.

## Remaining Limitations

The PostgreSQL concurrency test requires `DATABASE_URL` and a migrated database. SQLite cannot validate row-level lock semantics.
