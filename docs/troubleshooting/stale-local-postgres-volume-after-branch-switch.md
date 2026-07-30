# Stale Local PostgreSQL Volume After Branch Switch

## Problem

After switching between branches that changed SQLAlchemy models and Alembic migrations, local PostgreSQL may contain tables from one branch while Alembic revision state reflects another branch.

## Impact

Migration and PostgreSQL-backed tests can fail even when the current branch code is valid. Observed failures included:

- `psycopg.errors.DuplicateTable: relation "categories" already exists`
- `psycopg.errors.UndefinedColumn: column group_members.status does not exist`

## Reproduction

1. Run Docker Compose tests or migrations on a branch with one DB schema.
2. Switch to a different branch whose migrations differ.
3. Reuse the same named Docker volume.
4. Run `alembic upgrade head` or PostgreSQL-backed tests.

## Cause

The local named PostgreSQL volume persists across branches. Alembic revision metadata and actual tables can become inconsistent when branches introduce migrations and model changes in different orders.

## Alternatives Considered

- Debug and manually repair the local schema.
- Stamp Alembic revisions manually.
- Reset the local PostgreSQL volume.

Manual repair or stamping can hide real migration problems. For local verification, resetting the development volume is clearer.

## Resolution

Reset the local development database volume:

```bash
make reset CONFIRM=1
```

This stops containers, removes the local PostgreSQL volume, starts services again, and runs migrations from an empty database.

## Verification

After reset, Alembic applied all migrations from base to head successfully.

## Remaining Limitations

This deletes local development data. Do not use it for shared, staging, or production databases.
