# Secrets and Key Management

## Rules

- Secrets must not be committed to Git.
- Local secrets belong in `.env`.
- `.env.example` may contain key names and safe defaults only.
- LLM API keys must be loaded from environment variables or managed secret storage.

## Current Secret Inputs

- `LLM_API_KEY`
- `DATABASE_URL` when it contains non-local credentials

## Rotation

Rotation procedure is not implemented in Phase 0. Any production use requires a documented rotation and revocation process.
