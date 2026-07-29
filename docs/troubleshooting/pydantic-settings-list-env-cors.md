# Pydantic Settings List Env CORS Parsing

## Problem

`make dev` failed while starting the backend after `CORS_ALLOWED_ORIGINS=http://localhost:5173` was passed through Docker Compose.

## Impact

The backend container became unhealthy and `make dev` could not reach migration or health-check steps.

## Reproduction

```bash
make init
make dev
```

Backend startup failed with a `pydantic_settings.exceptions.SettingsError` while parsing `cors_allowed_origins`.

## Cause

`pydantic-settings` attempts to parse complex types such as `list[str]` from environment variables as JSON before normal validators run. The documented local value is a comma-separated string, not JSON.

## Alternatives Considered

- Require JSON array syntax in `.env`.
- Keep comma-separated `.env` syntax and parse it through a string setting.

## Resolution

`Settings.cors_allowed_origins` is stored as a string and exposed through `Settings.cors_origin_list`, which splits comma-separated origins for FastAPI CORS middleware.

## Verification

`make dev` should be rerun after this fix.

## Remaining Limitations

Complex list settings should avoid raw `list[...]` types unless the `.env` format is intentionally JSON.
