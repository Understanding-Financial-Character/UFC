# ADR-0004. Backend Security Baseline

## Status

Accepted

## Context

BE Phase 3 must add authentication, authorization, encryption, and secret handling before UFC stores transaction rows, financial behavior patterns, or generated financial reports.

## Decision

- Use Argon2id for password hashing through `argon2-cffi`.
- Issue signed bearer access tokens and opaque random refresh tokens.
- Store only refresh token SHA-256 hashes.
- Use `USER` and `ADMIN` roles only for MVP.
- Replace Phase 2 `X-UFC-User-Id` with authenticated bearer-token principal checks.
- Encrypt sensitive text fields with AES-256-GCM through a `KeyProvider` interface.
- Store searchable email as `email_ciphertext`, `email_lookup_hmac`, and `email_key_version`.
- Load auth and encryption secrets from environment settings and fail application startup when required secrets are missing or invalid.
- Restrict CORS origins through configuration.

## Consequences

- Existing Phase 2 users without email/password cannot authenticate until migrated through a later account migration path.
- Admin list responses may include masked email only; raw email and ciphertext fields are not returned.
- The current `EnvironmentKeyProvider` is intentionally small so a future KMS-backed provider can replace it without changing domain code.
- Login rate limiting is in-memory for MVP and must be replaced with shared storage before multi-process production deployment.
