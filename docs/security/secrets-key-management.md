# Secrets and Key Management

## Rules

- Secrets must not be committed to Git.
- Local secrets belong in `.env`.
- `.env.example` may contain key names and safe defaults only.
- LLM API keys must be loaded from environment variables or managed secret storage.

## Current Secret Inputs

- `LLM_API_KEY`
- `DATABASE_URL` when it contains non-local credentials
- `AUTH_TOKEN_SECRET`
- `FIELD_ENCRYPTION_KEY`
- `FIELD_LOOKUP_HMAC_KEY`
- `FIELD_KEY_VERSION`

`FIELD_ENCRYPTION_KEY` must be base64 encoded and decode to exactly 32 bytes for AES-256-GCM.

`AUTH_TOKEN_SECRET` and `FIELD_LOOKUP_HMAC_KEY` must each be at least 32 bytes. Generate non-local values with `openssl rand -base64 32` or an equivalent secret generator.

BE Phase 3 fails application startup when required auth or encryption settings are missing or invalid.

`compose.dev.yaml` requires these environment variables to be present. It does not provide committed fallback secret values.

## Key Provider

BE Phase 3 introduces a `KeyProvider` interface and an environment-backed implementation. Future production hardening can replace it with KMS without changing the domain APIs.

## Rotation

Rotation procedure is not implemented in Phase 0. Any production use requires a documented rotation and revocation process.

BE Phase 3 stores `email_key_version` so encrypted records can be associated with the key version used for encryption.
