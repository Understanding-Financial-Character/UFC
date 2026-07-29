# Backend Alembic Enum Duplication

## Problem

Running `docker compose -f compose.yaml -f compose.dev.yaml run --rm backend alembic upgrade head` failed during the BE Phase 2 migration.

## Impact

The Phase 2 PostgreSQL schema could not be applied, blocking reproducible deployment of the user, group, member, and personality tables.

## Reproduction

Run:

```bash
docker compose -f compose.yaml -f compose.dev.yaml run --rm backend alembic upgrade head
```

The failure raised `psycopg.errors.DuplicateObject: type "relationship_type" already exists`.

## Cause

The migration explicitly created PostgreSQL enum types and then passed the same enum objects into `op.create_table`. SQLAlchemy's PostgreSQL enum DDL hook also tried to create the enum while creating the table.

## Alternatives Considered

- Keep explicit enum creation and disable enum creation on table columns.
- Remove explicit enum creation and let SQLAlchemy/Alembic create enum types with the first table that uses them.

## Resolution

Removed the explicit enum `create()` calls from the migration and kept enum dropping in downgrade after dependent tables are dropped.

## Verification

`docker compose -f compose.yaml -f compose.dev.yaml run --rm backend alembic upgrade head` passed against PostgreSQL after the change.

## Remaining Limits

The migration is the first schema revision, so downgrade has not been exercised as part of the documented BE Phase 2 verification.
