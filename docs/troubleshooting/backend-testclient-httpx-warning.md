# Backend TestClient httpx Deprecation Warning

## Problem

Running backend pytest in Docker emits a `StarletteDeprecationWarning` from `fastapi.testclient`.

## Impact

Tests pass, but future Starlette or httpx releases may change the supported test client dependency path.

## Reproduction

```bash
docker compose -f compose.yaml -f compose.dev.yaml run --rm backend pytest
```

Observed warning:

```text
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
```

## Cause

The FastAPI version currently resolved in the backend Docker image imports Starlette's `TestClient`, which warns about the installed `httpx` package path.

## Alternatives Considered

- Keep `httpx` for now because FastAPI `TestClient` works and all tests pass.
- Replace the test client dependency with `httpx2` immediately.
- Pin FastAPI, Starlette, and httpx versions more tightly.

## Resolution

Keep the current dependency set for BE Phase 1 and record the warning. The warning does not block the foundation tests.

## Verification

Backend tests pass:

```text
5 passed, 1 warning
```

## Remaining Limitations

Before production hardening or CI enforcement with warnings-as-errors, revisit the FastAPI, Starlette, and httpx dependency set.
