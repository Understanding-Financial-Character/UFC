# Development Setup

## Prerequisites

- Docker Desktop or Docker Engine with Compose v2
- Python 3 for `scripts/bootstrap_env.py`
- `make`
- `curl`

## First Run

```bash
make dev
```

`make dev` runs:

1. `make init`
2. Docker Compose config validation
3. Service builds
4. `db`, `backend`, and `frontend` startup
5. PostgreSQL readiness wait
6. Alembic upgrade
7. Backend `/health` and `/ready` checks
8. Frontend availability check
9. Service status output

## Environment File

`make init` creates `.env` from `.env.example` only when `.env` is missing. It generates missing local secrets without overwriting existing values:

- `AUTH_TOKEN_SECRET`
- `FIELD_ENCRYPTION_KEY`
- `FIELD_LOOKUP_HMAC_KEY`
- `FIELD_KEY_VERSION`

`FIELD_ENCRYPTION_KEY` is base64-encoded 32 bytes.

## Verification

```bash
make verify
```

This checks Compose config, migrations, backend tests, backend lint, frontend lint/build, and whitespace.

## Optional AI Runtime

Ollama is not part of the default `make dev` path. AI Phase 1 adds a local runtime boundary and optional commands for Qwen3 4B.

```bash
make ai-setup
```

Additional AI commands:

```bash
make ai-up
make ai-pull
make ai-health
make ai-smoke
make verify-ai
```

The Ollama image is pinned through `OLLAMA_IMAGE` instead of using `latest`. `qwen3:4b` is pulled only when it is missing.

Backend provider settings:

- `LLM_PROVIDER=ollama`
- `LLM_BASE_URL=http://ollama:11434`
- `LLM_MODEL=qwen3:4b`
- `LLM_THINKING_ENABLED=false`
- `LLM_TEMPERATURE=0.2`
- `LLM_TIMEOUT_SECONDS=30`

Use `LLM_PROVIDER=ollama_with_template_fallback` only when the caller wants Ollama failures to return deterministic template text instead of propagating typed exceptions.

## Nginx

Nginx is deferred until Integration/Delivery phases. It is not part of default `make dev`.
