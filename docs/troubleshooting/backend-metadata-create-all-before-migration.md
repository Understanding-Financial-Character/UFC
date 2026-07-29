# Backend Metadata Create-All Before Migration

## Problem

During BE Phase 3 development, PostgreSQL integration tests were run before `alembic upgrade head`. The test helper used `Base.metadata.create_all()`, which can create newly added tables without applying Alembic's full column and constraint migration sequence.

## Impact

The development database reached a partial schema state: `refresh_tokens` existed, but the `users` table was still missing Phase 3 columns such as `email_ciphertext`. A later `alembic upgrade head` then failed with `relation "refresh_tokens" already exists`.

## Reproduction

1. Start from a PostgreSQL volume migrated only through BE Phase 2.
2. Run PostgreSQL API tests that call `Base.metadata.create_all()` after BE Phase 3 models are loaded.
3. Run:

```bash
docker compose -f compose.yaml -f compose.dev.yaml run --rm backend alembic upgrade head
```

## Cause

`Base.metadata.create_all()` is useful for isolated SQLite tests, but it is not a replacement for migrations on a long-lived PostgreSQL database. It creates missing tables and does not alter existing tables to match model changes.

## Alternatives Considered

- Drop the local PostgreSQL volume and rerun migrations from scratch.
- Require all PostgreSQL tests to run only after Alembic.
- Make the Phase 3 migration tolerate this known partial development state.

## Resolution

The Phase 3 migration now checks for existing columns, constraints, tables, and indexes before creating them. PostgreSQL integration tests also skip when the Phase 3 columns have not been migrated yet.

## Verification

After the migration guard was added, `alembic upgrade head` can proceed on a development database where `refresh_tokens` was created early.

## Remaining Limits

This guard handles the known Phase 3 development partial state. Production and CI should still run Alembic migrations before PostgreSQL API tests and should not rely on `Base.metadata.create_all()` for schema management.
