# Stale Frontend Image After Package Change

## Problem

After pulling a branch that changes `frontend/package.json` or `frontend/package-lock.json`, `make verify` can fail during frontend build with missing module/type errors.

Observed examples:

- `Cannot find module '@reduxjs/toolkit/query/react'`
- `Cannot find module 'react-redux'`
- `Cannot find module 'react-router-dom'`

## Impact

Backend tests and lint can pass, but frontend build fails because the local Docker image still contains an older `node_modules` install.

## Reproduction

1. Build or run the frontend Docker image on an older branch.
2. Pull a branch that adds frontend dependencies.
3. Run `make verify` without rebuilding the frontend image.

## Cause

The existing local Docker image can be reused even though frontend dependency files changed. The container then runs TypeScript against source files that require packages missing from the image.

## Alternatives Considered

- Delete all Docker images.
- Run `npm install` on the host.
- Rebuild only the project frontend image.

Rebuilding only the frontend image is the narrowest fix.

## Resolution

```bash
docker compose -f compose.yaml -f compose.dev.yaml build frontend
make verify
```

## Verification

After rebuilding `frontend`, `make verify` completed successfully.

## Remaining Limitations

`npm install` may report dependency audit warnings. Treat those separately from stale image repair.
